from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from employees.models import Employee
from .serializers import EmployeeRegisterSerializer, EmployeeSerializer
from .permissions import TopManagerUser
from commerce.utils.base_views import StandardizedResponseMixin


class RegisterEmployee(StandardizedResponseMixin, mixins.CreateModelMixin,
                   generics.GenericAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeRegisterSerializer
    permission_class = [TopManagerUser]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.save()

            # 🔐 Set is_staff = True for manager roles
            role = request.data.get("role")
            if role in ["Customer_Service_Manager", "Top_Manager"]:
                employee.is_staff = True
                employee.save()

            # 🔑 Generate JWT tokens
            refresh = RefreshToken.for_user(employee)

            # 📤 Build response
            response_data = {
                "message": "Employee registered successfully",
                "data": self.get_serializer(employee).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }
            return self.success_response(data=response_data, status_code=status.HTTP_201_CREATED, message="success")

        return self.error_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST, message="fail")
    
    
class ListEmployees(StandardizedResponseMixin, mixins.ListModelMixin,
                    generics.GenericAPIView):
    queryset = Employee.objects.all()  
    serializer_class = EmployeeSerializer
    permission_class = [TopManagerUser] 
    
    def get(self, request, *args, **kwargs):
        data = self.list(request, *args, **kwargs) 
        return self.success_response(data= data.data, message= "success") 