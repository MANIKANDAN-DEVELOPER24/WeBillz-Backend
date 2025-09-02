# sales/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal

class User(AbstractUser):
    ROLE_CHOICES = (("admin", "Admin"), ("staff", "Staff"))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="staff")
    counter = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Product(models.Model):
    id = models.CharField(max_length=100, primary_key=True)  # allows 'p-apple-250'
    name = models.CharField(max_length=200)
    hsn = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    gstPct = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Sale(models.Model):
    MODE_CHOICES = (("Cash", "Cash"), ("Card", "Card"), ("UPI", "UPI"))
    date = models.DateTimeField(auto_now_add=True)
    counter = models.PositiveIntegerField()
    staff = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    taxable = models.DecimalField(max_digits=12, decimal_places=2)
    gst = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="Cash")
    product_snapshot = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Sale {self.pk} - {self.product.name}"
