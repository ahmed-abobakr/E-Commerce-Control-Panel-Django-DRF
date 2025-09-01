from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from categories.models import Category
from employees.models import Employee

class Product(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=150, null=True)
    brand = models.CharField(max_length=50, null=True)
    stock_count = models.IntegerField(default=0)
    price = models.FloatField(default=0.0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='product', default=1)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, default=1)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.title} has {self.stock_count} in stocks"
    

