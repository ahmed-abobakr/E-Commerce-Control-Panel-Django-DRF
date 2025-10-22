from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductReadOnlyViewSet, ProductViewSet, RestockAdvisorView

router = DefaultRouter()
router.register('manage_products', ProductViewSet, basename='manageproducts')
router.register('get_products', ProductReadOnlyViewSet, basename='getproducts')

urlpatterns = [
    path('', include(router.urls)),
    path('min_products_stock/', RestockAdvisorView.as_view()),
]