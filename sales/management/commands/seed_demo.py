# core/management/commands/seed_demo.py
from django.core.management.base import BaseCommand
from sales.models import Product, User

class Command(BaseCommand):
    help = "Seed demo users and products"

    def handle(self, *args, **options):
        users = [
            {"username": "admin", "password": "admin123", "first_name": "Admin", "role": "admin", "is_staff": True, "is_superuser": True},
            {"username": "c1", "password": "c1", "first_name": "Counter 1", "role": "staff", "counter": 1},
            {"username": "c2", "password": "c2", "first_name": "Counter 2", "role": "staff", "counter": 2},
            {"username": "c3", "password": "c3", "first_name": "Counter 3", "role": "staff", "counter": 3},
        ]
        for u in users:
            user, created = User.objects.get_or_create(username=u["username"])
            user.first_name = u.get("first_name", "")
            user.role = u.get("role", "staff")
            user.counter = u.get("counter", None)
            user.is_staff = u.get("is_staff", False)
            user.is_superuser = u.get("is_superuser", False)
            if u.get("password"):
                user.set_password(u["password"])
            user.save()
            self.stdout.write(f"User {user.username} {'created' if created else 'updated'}")

        products = [
            {"id": "p-apple-250", "name": "7 Up 250ml", "hsn": "2202", "price": "41.00", "gstPct": "12.00", "stock": 12},
            {"id": "p-orange-250", "name": "Frooti 250ml", "hsn": "2202", "price": "50.00", "gstPct": "15.00", "stock": 0},
            {"id": "p-mango-500", "name": "Maaza 500ml", "hsn": "0403", "price": "90.00", "gstPct": "18.00", "stock": 7},
            {"id": "p-lime-100", "name": "Sprite 300ml", "hsn": "2202", "price": "41.00", "gstPct": "14.00", "stock": 5},
        ]
        for p in products:
            obj, created = Product.objects.update_or_create(id=p["id"], defaults=p)
            self.stdout.write(f"Product {obj.id} {'created' if created else 'updated'}")

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
