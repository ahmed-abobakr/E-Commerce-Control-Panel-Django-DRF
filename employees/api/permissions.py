from rest_framework.permissions import BasePermission, SAFE_METHODS


class CustomerServiceManagerOrTopManagerUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        print(f"permission request.user.role: {request.user.role}")
        if request.method in SAFE_METHODS:
            return True
        return hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager",
            "Customer_Service_Manager"
        ]
        
        
class TopManagerUser(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return hasattr(request.user, 'role') and request.user.role  == "Top_Manager"     
        
        
class CustomerServiceUserOrTopManagerUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager",
            "Customer_Service_Manager",
            "Customer_Service"
        ]        