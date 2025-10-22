from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderListViewSet, DiscountMessageView, OrderExplainMessageView

router = DefaultRouter()
router.register('orders', OrderListViewSet,basename='orders')

urlpatterns = [
    path('', include(router.urls)),
    path('discounts/', DiscountMessageView.as_view()),
    path('order_message/', OrderExplainMessageView.as_view()),
]