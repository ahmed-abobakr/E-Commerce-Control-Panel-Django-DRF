from rest_framework import viewsets
from products.models import Product
from .serializers import ProductSerializer
from .pagination import ProductPagination
from employees.api.permissions import CustomerServiceManagerOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin

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
        return self.success_response(data=response.data, message="success", status_code=201)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return self.success_response(data=None, message="success", status_code=204)
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

        