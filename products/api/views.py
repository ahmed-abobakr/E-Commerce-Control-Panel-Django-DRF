from rest_framework import viewsets
from products.models import Product
from .serializers import ProductSerializer
from .pagination import ProductPagination
from employees.api.permissions import CustomerServiceManagerOrTopManagerUserOrReadOnly

class ProductReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    
    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    permission_class = [CustomerServiceManagerOrTopManagerUserOrReadOnly]
        