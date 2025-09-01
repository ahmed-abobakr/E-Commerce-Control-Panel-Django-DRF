from rest_framework import serializers
from customers.models import Customer

class CustomerSerilazer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        exclude = ('username', 'password', 'last_login', 'is_superuser', 'is_staff',
                   'is_active', 'groups', 'user_permissions')