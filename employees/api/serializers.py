from rest_framework import serializers
from employees.models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        execlude = ('username', 'password')
        
        
class EmployeeLoginSerializer(serializers.ModelSerialier):
    class Metal:
        model = Employee
        fields = '__all__'        