from django.core.exceptions import PermissionDenied
from customers.models import Customer
from django.db import models  

def list_customers(request):
    """
        return all customers
    """
    if hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager",
            "Customer_Service_Manager",
            "Customer_Service"
        ] == False:
        
        raise PermissionDenied()
    return Customer.objects.all()

def get_customer(request, customer_id):
    """
        return customer with id = customer_id
    """
    if hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager",
            "Customer_Service_Manager",
            "Customer_Service"
        ] == False:
        
        raise PermissionDenied()
    return Customer.objects.filter(id=customer_id).first()


def search_customers(request, name: str, phone: str = None, address: str = None):
    """
    Search customers by name with optional phone/address filters
    Args:
        request: Django Request Object
        name: Customer name (partial match)
        phone: Phone number (optional, partial match)
        address: Address (optional, partial match)

    Returns:
        cutomer
    """
    if hasattr(request.user, 'role') and request.user.role not in [
        "Top_Manager",
        "Customer_Service_Manager",
        "Customer_Service"
    ]:
        raise PermissionDenied()

    name_parts = name.split()
    
    if len(name_parts) == 1:
        queryset = Customer.objects.filter(
            models.Q(first_name__icontains=name_parts[0])
        )
    else:
        queryset = Customer.objects.filter(
            models.Q(first_name__icontains=name_parts[0]) &
            models.Q(last_name__icontains=name_parts[1])
        )
    print(f"search customer queryset byName: {name} {queryset}")
    if phone:
        queryset = queryset.filter(phone__icontains=phone)
    
    if address:
        queryset = queryset.filter(address__icontains=address)
    print(f"search customer queryset: {queryset}")
    return queryset