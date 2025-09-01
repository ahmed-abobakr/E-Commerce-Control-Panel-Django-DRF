from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryReadOnlyViewSet, CategoryViewSet


router = DefaultRouter()
router.register('manage_categories', CategoryViewSet, basename = 'managecategories')
router.register('get_categories', CategoryReadOnlyViewSet, basename = 'getcategories')

urlpatterns = [
    path('', include(router.urls)),
]
