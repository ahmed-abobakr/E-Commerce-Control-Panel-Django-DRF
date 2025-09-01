from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Employee(User):
    CUST_SERVICE = "Customer_Service"
    CUST_SERVICE_MANAGER = "Customer_Service_Manager"
    DATA_ANALYIST = "Data_Analyst"
    TOP_MANAGER = "Top_Manager"
    EMPLOYEE_ROLES = {
        CUST_SERVICE: "Customer Service",
        CUST_SERVICE_MANAGER: "Customer Service Manager",
        DATA_ANALYIST: "Data Analyst",
        TOP_MANAGER: "Top Manager"
    }
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, choices=EMPLOYEE_ROLES, null=True, default=None)
    created_at = models.DateField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} works as {self.role}"
