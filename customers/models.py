from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.

class Customer(User):
    phone = models.CharField(max_length=40)
    address1 = models.CharField(max_length=300)
    address2 = models.CharField(max_length=300, null=True, blank=True)
    address3 = models.CharField(max_length=300, null=True, blank=True)
    address4 = models.CharField(max_length=300, null=True, blank=True)
    
    def __str__(self):
        return f"Customer {self.first_name} {self.last_name}"
    
