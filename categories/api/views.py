from rest_framework import viewsets
from categories.models import Category
from .serializers import CategorySerializer
from employees.api.permissions import CustomerServiceUserOrTopManagerUserOrReadOnly

class CategoryReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]    