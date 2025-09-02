# sales/serializers.py
from rest_framework import serializers
from .models import User, Product, Sale
from django.contrib.auth.hashers import make_password
from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    # expose frontend-friendly id like "u-<username>" and name
    id = serializers.SerializerMethodField(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "name", "first_name", "last_name", "role", "counter", "password")
        extra_kwargs = {"password": {"write_only": True, "required": False}}

    def get_id(self, obj):
        return f"u-{obj.username}"

    def get_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.username

    def create(self, validated_data):
        pwd = validated_data.pop("password", None)
        user = super().create(validated_data)
        if pwd:
            user.set_password(pwd)
            user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if pwd:
            user.set_password(pwd)
            user.save()
        return user


class CreateStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password", "first_name", "last_name", "counter")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role="staff",
            counter=validated_data.get("counter", None),
        )
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "hsn", "price", "gstPct", "stock")


class SaleSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.CharField(write_only=True)
    staff = serializers.SerializerMethodField(read_only=True)
    staffId = serializers.SerializerMethodField(read_only=True)
    totals = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Sale
        fields = ("id", "date", "counter", "staff", "staffId", "product", "product_id", "qty", "discount", "totals", "mode")
        read_only_fields = ("date", "counter", "staff", "staffId", "product", "totals")

    def get_staff(self, obj):
        return obj.staff.get_full_name() or obj.staff.username

    def get_staffId(self, obj):
        return f"u-{obj.staff.username}"

    def get_totals(self, obj):
        return {"taxable": float(obj.taxable), "gst": float(obj.gst), "total": float(obj.total)}
