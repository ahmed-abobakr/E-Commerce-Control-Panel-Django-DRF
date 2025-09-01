from rest_framework import serializers
from customers.models import Customer

class CustomerSerilazer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        execlude = ('username', 'password')