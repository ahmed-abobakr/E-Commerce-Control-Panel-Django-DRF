from rest_framework import viewsets
from orders.models import Order, OrderItems
from .serializers import OrderSerializer, OrderItemsSerializer
from .pagination import OrderPagination
from employees.api.permissions import CustomerServiceUserOrTopManagerUserOrReadOnly
from commerce.utils.base_views import StandardizedResponseMixin


class OrderListViewSet(StandardizedResponseMixin, viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemsSerializer
    pagination_class = OrderPagination
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]
    
    
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
