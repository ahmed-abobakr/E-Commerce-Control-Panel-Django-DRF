from django.urls import path
from .views import RegisterEmployee

urlpatterns = [
    path('add_employee/', RegisterEmployee.as_view(), name='add-employee'),
]