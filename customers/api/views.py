from rest_framework import generics, mixins
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerilazer
from customers.models import Customer
from .permissions import CustomerServiceUserOrTopManagerUser
from commerce.utils.base_views import StandardizedResponseMixin
from commerce.utils.build_chunks import insert_customer_chunks


class CustomerList(StandardizedResponseMixin,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   generics.GenericAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerilazer
    permission_class = [CustomerServiceUserOrTopManagerUser]
    
    def get(self, request, *args, **kwargs):
        data = self.list(request, *args, **kwargs)
        insert_customer_chunks(data.data) 
        return self.success_response(data= data.data, message= "success")
        

    def post(self, request, *args, **kwargs):
        data = self.create(request, *args, **kwargs)
        
        return self.success_response(data=data.data, message="success")
    
    
class CustomerDetail(StandardizedResponseMixin,
                    mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   generics.GenericAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerilazer
    permission_class = [CustomerServiceUserOrTopManagerUser]

    def get(self, request, *args, **kwargs):
        data = self.retrieve(request, *args, **kwargs)
        return self.success_response(data=data.data, message="success")
    def put(self, request, *args, **kwargs):
        data= self.update(request, *args, **kwargs)
        return self.success_response(data=data.data, message="success")
    
    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return self.success_response(data=None, message="success", status_code=status.HTTP_204_NO_CONTENT)    