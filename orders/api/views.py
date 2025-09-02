from rest_framework import viewsets
from orders.models import Order, OrderItems
from .serializers import OrderSerializer, OrderItemsSerializer
from .pagination import OrderPagination
from employees.api.permissions import CustomerServiceUserOrTopManagerUserOrReadOnly


class OrderListViewSet(viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemsSerializer
    pagination_class = OrderPagination
    permission_class = [CustomerServiceUserOrTopManagerUserOrReadOnly]