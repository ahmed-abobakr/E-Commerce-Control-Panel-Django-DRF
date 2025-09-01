from rest_framework import serializers
from orders.models import Order, OrderItems
from products.api.serializers import ProductSerializer
from customers.api.serializers import CustomerSerilazer
from products.models import Product
from orders.models import Order

class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerilazer(read_only=True)
    class Meta:
        model = Order
        fields = '__all__'
        
class OrderItemsSerializer(serializers.ModelSerializer):
    order_detail = OrderSerializer(source='order', read_only=True)
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), write_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
    
    class Meta:
        model = OrderItems
        fields = ['id', 'quantity', 'order_detail', 'order', 'product', 'product_detail']        