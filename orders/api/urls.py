from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderListViewSet

router = DefaultRouter()
router.register('orders', OrderListViewSet,basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]