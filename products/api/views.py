from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response


from products.models import Product
from .serializers import ProductSerializer
from .pagination import ProductPagination
from employees.api.permissions import CustomerServiceManagerOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin
from commerce.utils.build_chunks import insert_product_chunks
from commerce.services.rag import build_restock_prompt, search_admin_chunks, llm_chat

class ProductReadOnlyViewSet(StandardizedResponseMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")
    
    
class ProductViewSet(StandardizedResponseMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    permission_class = [CustomerServiceManagerOrTopManagerUserOrReadOnly]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        try:
            print("view before insert product chunks")
            message = insert_product_chunks(response.data)
        except Exception as e:
            print(f"Error creating product: {e}")
            message = "Error building product chunks"
        print(message)    
        return self.success_response(data=response.data, message="success", status_code=201)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return self.success_response(data=None, message="success", status_code=204)
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

class RestockAdvisorView(APIView):
    """
    Query params:
      category (required) -> category name
      threshold (default 50)
      k (default 10) -> top semantic ranking after SQL filter
      q (optional) -> semantic intent, e.g. "top hair care restock"
    """
    permission_class = [CustomerServiceManagerOrTopManagerUserOrReadOnly]

    def get(self, request):
        cat_name = request.query_params.get("category")
        if not cat_name:
            return Response({"error": "category is required"}, status=400)

        threshold = int(request.query_params.get("threshold", 50))
        k = int(request.query_params.get("k", 10))
        q = request.query_params.get("q", f"restock candidates for category {cat_name}")

        # SQL pre-filter: low stock & high rating in category
        qs = (Product.objects
              .filter(category=cat_name, stock_count__lt=threshold)
              .values("id", "title", "stock_count", "price", "rating")
              .order_by("stock_count"))

        rows = list(qs)
        print(f"result: {rows}")
        if not rows:
            return Response({"count": 0, "data": [], "advice": None})

        # Semantic rank over admin_chunk (entity_type=product) using q
        retrieved = search_admin_chunks(q, k=50, entity_type="product")
        # Prioritize items present in rows
        ids = {r["id"] for r in rows}
        ranked = [c for c in retrieved if c["entity_id"] in ids][:k]

        advice = build_restock_prompt(cat_name, rows, ranked)

        return Response({
            "count": len(rows),
            "filtered": rows[:50],  # preview
            "top_ranked": [{"product_id": c["entity_id"], "source": c["source"], "distance": c["distance"]}
                           for c in ranked],
            "advice": advice
        })        