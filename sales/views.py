# sales/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import csv

from .models import Product, Sale, User
from .serializers import ProductSerializer, SaleSerializer, UserSerializer, CreateStaffSerializer
from .permissions import IsAdmin, IsStaffOrAdmin

# ---- Auth endpoints ----
class CreateUserByAdminView(generics.CreateAPIView):
    """
    POST /api/auth/register/  (Admin only)  -- create admin or staff
    """
    queryset = User.objects.all()
    serializer_class = CreateStaffSerializer
    permission_classes = [IsAdmin]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """ GET /api/auth/profile/ """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# We will provide custom token view in urls (see below) using SimpleJWT

# ---- Products ----
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("name")
    serializer_class = ProductSerializer

    def get_permissions(self):
        # list/retrieve: any authenticated user
        # create/update/destroy: admin only
        if self.action in ("create", "update", "partial_update", "destroy"):
            permission_classes = [IsAuthenticated, IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]


# ---- Sales ----
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
import csv
from decimal import Decimal

from .models import Sale, Product
from .serializers import SaleSerializer
from .permissions import IsAdmin, IsStaffOrAdmin  # make sure IsStaffOrAdmin = staff OR admin


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related("product", "staff").all().order_by("-date")
    serializer_class = SaleSerializer

    def get_permissions(self):
        """Define permissions per action"""
        if self.action in ["list", "daily_report"]:
            perms = [IsAuthenticated, IsAdmin]           # admin only
        elif self.action == "create":
            perms = [IsAuthenticated, IsStaffOrAdmin]    # staff + admin
        else:
            perms = [IsAuthenticated, IsAdmin]           # lock down other actions to admin only
        return [p() for p in perms]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = request.data
        product_id = data.get("product_id")
        qty = int(data.get("qty", 0))
        discount = Decimal(str(data.get("discount", "0") or "0"))
        mode = data.get("mode", "Cash")

        if qty <= 0:
            return Response({"detail": "qty must be >= 1"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                product = Product.objects.select_for_update().get(pk=product_id)
            except Product.DoesNotExist:
                return Response({"detail": "product not found"}, status=status.HTTP_404_NOT_FOUND)

            if product.stock < qty:
                return Response({"detail": "insufficient stock"}, status=status.HTTP_400_BAD_REQUEST)

            price = product.price
            subtotal = (price * qty) - discount
            taxable = max(Decimal("0.00"), subtotal)
            gst = (taxable * product.gstPct) / Decimal("100.00")
            total = (taxable + gst).quantize(Decimal("0.01"))

            sale = Sale.objects.create(
                counter=getattr(request.user, "counter", 0) or 0,
                staff=request.user,
                product=product,
                qty=qty,
                discount=discount,
                taxable=taxable,
                gst=gst,
                total=total,
                mode=mode,
                product_snapshot={
                    "id": product.id,
                    "name": product.name,
                    "price": float(product.price),
                    "gstPct": float(product.gstPct),
                }
            )

            # decrement stock
            product.stock -= qty
            product.save()

            serializer = self.get_serializer(sale)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def daily_report(self, request):
        """GET /api/sales/daily-report/?date=YYYY-MM-DD"""
        date_str = request.query_params.get("date")
        if date_str:
            try:
                date_obj = timezone.datetime.fromisoformat(date_str).date()
            except Exception:
                return Response({"detail": "invalid date format, use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            date_obj = timezone.localdate()

        start = timezone.datetime.combine(date_obj, timezone.datetime.min.time()).replace(tzinfo=timezone.utc)
        end = timezone.datetime.combine(date_obj, timezone.datetime.max.time()).replace(tzinfo=timezone.utc)

        qs = Sale.objects.filter(date__range=(start, end)).select_related("staff", "product")

        # build CSV
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="sales-{date_obj.isoformat()}.csv"'

        writer = csv.writer(response)
        header = ["date", "counter", "staff", "product", "qty", "price", "discount", "taxable", "gst", "total"]
        writer.writerow(header)
        for s in qs:
            writer.writerow([
                s.date.isoformat(),
                s.counter,
                s.staff.get_full_name() or s.staff.username,
                s.product.name,
                s.qty,
                str(s.product.price),
                str(s.discount),
                str(s.taxable),
                str(s.gst),
                str(s.total),
            ])
        return response

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Returns the currently logged-in user (from JWT token).
    """
    user = request.user
    return Response({
        "id": str(user.id),
        "username": user.username,
        "name": getattr(user, "name", ""),      # if you have custom field
        "role": getattr(user, "role", ""),      # if you have role field
        "counter": getattr(user, "counter", None),  # if applicable
    })

from django.contrib.auth import get_user_model
from sales.serializers import UserSerializer
from rest_framework.views import APIView

User = get_user_model()

class StaffListView(APIView):
    permission_classes = [IsAuthenticated]  # only logged-in users

    def get(self, request):
        staff_users = User.objects.filter(role="staff")
        serializer = UserSerializer(staff_users, many=True)
        return Response(serializer.data)