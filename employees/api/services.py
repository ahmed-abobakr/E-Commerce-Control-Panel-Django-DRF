from django.core.exceptions import PermissionDenied

from employees.models import Employee


def list_employess(request):
    """
        return all employees
    """
    if hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager"
        ] == False:
        
        raise PermissionDenied()
    return Employee.objects.all()


def get_employee(request, employee_id):
    """
        return employee with id = employee_id
    """
    if hasattr(request.user, 'role') and request.user.role in [
            "Top_Manager"
        ] == False:
        
        raise PermissionDenied()
    return Employee.objects.filter(id=employee_id).first()