from django.contrib import admin
from .models import Brand, Category, Product, CartItem


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price', 'rating', 'in_stock', 'created_at')
    list_filter = ('brand', 'category', 'in_stock')
    search_fields = ('name', 'description', 'brand__name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 25


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'session_id', 'product', 'quantity', 'added_at')
    search_fields = ('session_id', 'product__name', 'user__username')
    list_filter = ('user',)
