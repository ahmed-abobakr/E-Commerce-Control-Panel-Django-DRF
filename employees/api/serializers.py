from rest_framework import serializers
from employees.models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        #execlude = ('username', 'password')
        fields = '__all__'
        
        
class EmployeeRegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    class Meta:
        model = Employee
        fields = ['username', 'first_name', 'last_name','email', 'password', 'confirm_password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def save(self):
        password = self.validated_data['password']
        confirm_password = self.validated_data['confirm_password']
        if password != confirm_password:
            raise serializers.ValidationError({'error': 'Password and ConfirmPassword should be same'})

        if Employee.objects.filter(email=self.validated_data['email']).exists():
            raise serializers.ValidationError({'error': 'Email already exists'})

        account = Employee(first_name = self.validated_data['first_name'], last_name = self.validated_data['last_name'],
            email=self.validated_data['email'], username=self.validated_data['username'], role=self.validated_data['role'])
        account.set_password(password)
        account.save()
        return account      