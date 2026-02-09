from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied


from orders.models import Order, OrderItems
from .serializers import OrderItemsSerializer, OrderCreateSerializer
from employees.api.permissions import CustomerServiceUserOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin
from . import services
    


class OrderListViewSet(StandardizedResponseMixin, viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderItemsSerializer  # default serializer for GET, etc.
    
    def list(self, request, *args, **kwargs):
        print("first line of Orderlist function")
        queryset = self.get_queryset().select_related('order', 'product')
        orders_qs = Order.objects.filter(
            id__in=queryset.values_list('order_id', flat=True).distinct()
        ).order_by('id')
        page = self.paginate_queryset(orders_qs)
        data = services.get_paginated_orders_with_products(request, queryset, page)
        #paginated_response = self.get_paginated_response(data)
        return self.success_response(data=data, message="success")

        # If pagination is active, use DRF’s paginated response
        paginated_response = self.get_paginated_response(response_data)

        # Wrap it in standardized success response
        return self.success_response(
            data=paginated_response.data,
            message="success"
        )

    def retrieve(self, request, *args, **kwargs):
        data = services.get_order_with_products(request, self.get_object())
        return self.success_response(data=data, message="success")

    def create(self, request, *args, **kwargs):
        request_data = request.data.copy()
        request_data["created_by"] = request.user.id
        serializer = self.get_serializer(data=request_data)
        try:
            data = services.create_order_and_recommend(request, serializer)
            return self.success_response(data=data, message="success", status_code=201) 
        except PermissionDenied:
            return self.error_response(
                data=None,
                message="You are not authorized to create orders",
                status_code=403
            )

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
        amount_min = float(request.query_params.get("amount_min", 1000))
        k = int(request.query_params.get("k", 5))
        with_text = request.query_params.get("with_text") == "1"
        try:
            results = services.build_discount_messages(request, amount_min, k, with_text)
            return Response({"count": len(results), "data": results})
        except PermissionDenied:
            return Response({"error": "You are not authorized to get discount messages"}, status=403)
    
    
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
            result, error = services.get_order_explanation(request, order_id)
            if error:
                return Response(error, status=404)
            return Response(result)
        except PermissionDenied:
            return Response({"error": "You are not authorized to get order explanation"}, status=403)
