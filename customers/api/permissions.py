from rest_framework.permissions import BasePermission, SAFE_METHODS

class CustomerServiceUserOrTopManagerUser(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager",
            "Customer_Service_Manager",
            "Customer_Service"
        ]