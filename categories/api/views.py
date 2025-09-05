from rest_framework import viewsets
from categories.models import Category
from .serializers import CategorySerializer
from employees.api.permissions import CustomerServiceManagerOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin

class CategoryReadOnlyViewSet(StandardizedResponseMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success_response(data=response.data, message="success")
    
    
class CategoryViewSet(StandardizedResponseMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
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
        super().update(request, *args, **kwargs)
        return self.success_response(data=None, message="success", status_code=200)
