from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    ProductListView, ProductDetailView,
    BrandListView, CategoryListView,
    CartView, CartClearView
)

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/clear/", CartClearView.as_view(), name="cart-clear"),
    path("auth/token/", obtain_auth_token, name="api_token_auth"),
]
