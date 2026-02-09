from rest_framework import serializers
from products.models import Product
from categories.api.serializers import CategorySerializer
from categories.models import Category

class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    class Meta:
        model = Product
        fields = ['title', 'description', 'brand', 'stock_count', 'price', 'rating', 'category_detail', 'category']
        
        
class ProductReadSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    class Meta:
        model = Product
        fields = '__all__'      