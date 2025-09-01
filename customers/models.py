from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Customer(User):
    phone = models.CharField(max_length=20)
    address1 = models.CharField(max_length=300)
    address2 = models.CharField(max_length=300, null=True, blank=True)
    address3 = models.CharField(max_length=300, null=True, blank=True)
    address4 = models.CharField(max_length=300, null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
