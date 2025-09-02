# sales/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, Sale

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "role", "counter", "is_staff", "is_superuser")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "gstPct", "stock")

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "staff", "qty", "total", "date")
    readonly_fields = ("date",)
