from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum, F
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response


from orders.models import Order, OrderItems
from customers.models import Customer
from .serializers import OrderSerializer, OrderItemsSerializer, OrderCreateSerializer
from .pagination import OrderPagination
from employees.api.permissions import CustomerServiceUserOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin
from commerce.utils.build_chunks import insert_order_and_items_chunks
from commerce.services.rag import recommend_products_for_customer, build_recommendation_message, build_discount_message_for_customer, build_order_explain_prompt
    


class OrderListViewSet(StandardizedResponseMixin, viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    #serializer_class = OrderItemsSerializer
    pagination_class = OrderPagination
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]
    
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderItemsSerializer  # default serializer for GET, etc.
    
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()  # calls create() inside the serializer
        response = OrderSerializer(order)  # for clean output
        insert_order_and_items_chunks(response.data)
        try:
            customer = Customer.objects.get(id=response.data['customer']['id'])
        except Customer.DoesNotExist:
            msg = None

        recs, context = recommend_products_for_customer(customer, k=6)
        print(f"recs: {recs}")
        # Add new custom fields
        response_data = response.data.copy()
        response_data["recommended_products"] = [r['title'] for r in recs]

        
        response_data["recommendation_message"] = build_recommendation_message(customer, recs, context)
        return self.success_response(data=response_data, message="success", status_code=201)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return self.success_response(data=None, message="success", status_code=204)
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")
    
class DiscountMessageView(APIView):
    """
    Params:
      amount_min (default 1000)
      k (default 5)          -> how many items to suggest
      with_text=1            -> include composed message
    """
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]

    def get(self, request):
        t0 = now() - timedelta(days=7)
        amount_min = float(request.query_params.get("amount_min", 1000))
        k = int(request.query_params.get("k", 5))

        # Segment customers
        spend = (Order.objects
                 .filter(created_at__gte=t0, status__in=["Order_Finished","Order_Delivered"])
                 .values("customer_id")
                 .annotate(total_week=Sum("grand_price"))
                 .filter(total_week__gt=amount_min)
                 .order_by("-total_week"))
        print(f"spend: {spend}")
        results = []
        for row in spend:
            try:
                customer = Customer.objects.get(id=row["customer_id"])
            except Customer.DoesNotExist:
                continue
            recs, context = recommend_products_for_customer(customer, k=k)
            msg = None
            if request.query_params.get("with_text") == "1":
                msg = build_discount_message_for_customer(customer, recs, context, policy={
                    "discount_pct": 15,
                    "deadline": "3 days from now",
                    "exclusions": "excludes already discounted items"
                })
            results.append({
                "customer_id": customer.id,
                "customer_name": f"{customer.first_name} {customer.last_name}",
                "total_week": row["total_week"],
                "suggestions": recs,
                "message": msg
            })

        return Response({"count": len(results), "data": results})   
    
    
class OrderExplainMessageView(APIView):
    """
    Query params:
      order_id (required)
    Returns: customer-friendly Arabic message with evidence
    """
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]

    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response({"error": "order_id is required"}, status=400)

        try:
            o = (Order.objects
                 .select_related("customer")
                 .get(id=order_id))
        except Order.DoesNotExist:
            return Response({"error": "order not found"}, status=404)
        print(f"order: {o}")
        items = list(OrderItems.objects.filter(order=o)
                     .values("product__title", "quantity", "product__price"))
        # Build structured context (no sensitive PII)
        context_rows = [
            f"- {r['product__title']} x{r['quantity']} @ {r['product__price']}"
            for r in items
        ]
        order_snapshot = (
            f"Order#{o.id} | status={o.status} | payment={o.payment_status} | "
            f"grand={o.grand_price} | address={(o.address or '')[:64]}..."
        )

        

        data = build_order_explain_prompt(o, context_rows)
        

        return Response({
            "order_id": o.id,
            "message": data["message"],
            "evidence": [{"id": c["id"], "source": c["source"], "distance": c["distance"]} for c in data["retrieved"]]
        })     
