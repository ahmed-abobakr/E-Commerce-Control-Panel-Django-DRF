from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework import status
from employees.models import Employee
from .serializers import EmployeeRegisterSerializer, EmployeeSerializer
from .permissions import TopManagerUser


class RegisterEmployee(mixins.CreateModelMixin,
                   generics.GenericAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeRegisterSerializer
    permission_class = [TopManagerUser]
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)