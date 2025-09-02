from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerilazer
from customers.models import Customer
from .permissions import CustomerServiceUserOrTopManagerUser


class CustomerList(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   generics.GenericAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerilazer
    permission_class = [CustomerServiceUserOrTopManagerUser]
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs) 
        

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    
class CustomerDetail(mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   generics.GenericAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerilazer
    permission_class = [CustomerServiceUserOrTopManagerUser]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)    