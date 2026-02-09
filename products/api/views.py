from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied


from .services import (
    create_product, update_product, delete_product, get_restock_advice, list_products, get_product
)
from .serializers import ProductSerializer
from .pagination import ProductPagination
from employees.api.permissions import CustomerServiceManagerOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin

class ProductReadOnlyViewSet(StandardizedResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    
    def list(self, request, *args, **kwargs):
        queryset = list_products()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        paginated_data = self.get_paginated_response(serializer.data)
        return self.success_response(data=paginated_data.data, message="success")

    def retrieve(self, request, *args, **kwargs):
        product_id = kwargs.get("pk")
        product = get_product(product_id)
        if not product:
            return self.error_response(message="Product not found", status_code=404)

        serializer = self.get_serializer(product)
        return self.success_response(data=serializer.data, message="success")
    
    
class ProductViewSet(StandardizedResponseMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    permission_class = [CustomerServiceManagerOrTopManagerUserOrReadOnly]
    
    def list(self, request, *args, **kwargs):
        queryset = list_products()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        paginated_data = self.get_paginated_response(serializer.data)
        return self.success_response(data=paginated_data.data, message="success")

    def retrieve(self, request, *args, **kwargs):
        product_id = kwargs.get("pk")
        product = get_product(product_id)
        if not product:
            return self.error_response(message="Product not found", status_code=404)

        serializer = self.get_serializer(product)
        return self.success_response(data=serializer.data, message="success")
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["created_by"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            product = create_product(request, serializer.validated_data)
            serializer = self.get_serializer(product)
            return self.success_response(data=serializer.data, message="success", status_code=201)
        except PermissionDenied:
            return self.error_response(message="Permission denied", status_code=403)

    def destroy(self, request, *args, **kwargs):
        product_id = kwargs.get("pk")
        try:
            delete_product(request, product_id)
            return self.success_response(data=None, message="success", status_code=204)
        except PermissionDenied:
            return self.error_response(message="Permission denied", status_code=403)
    
    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        data["created_by"] = request.user.id
        product_id = kwargs.get("pk")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            product = update_product(request, product_id, serializer.validated_data)
            serializer = self.get_serializer(product)
            return self.success_response(data=serializer.data, message="success")
        except PermissionDenied:
            return self.error_response(message="Permission denied", status_code=403)

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
        try:
            advice_data = get_restock_advice(request, cat_name, threshold, k, q)
            return Response(advice_data)
        except PermissionDenied:
            return self.error_response(message="Permission denied", status_code=403)