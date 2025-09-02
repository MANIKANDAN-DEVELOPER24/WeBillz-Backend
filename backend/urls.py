# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import ProductViewSet, SaleViewSet, CreateUserByAdminView, profile_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from sales.serializers import UserSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from sales.views import me
from sales.views import StaffListView

# custom token serializer to include user info in login response
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # include user info
        data["user"] = {
            "id": f"u-{user.username}",
            "username": user.username,
            "name": user.get_full_name() or user.username,
            "role": user.role,
            "counter": user.counter,
        }
        return data

class MyTokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"sales", SaleViewSet, basename="sale")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", CreateUserByAdminView.as_view(), name="create-staff"),
    path("api/auth/login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("users/me/", me, name="user-me"),   # 👈 new endpoint
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/profile/", profile_view, name="profile"),
    path("api/users/", StaffListView.as_view(), name="staff-list"),
    path("api/", include(router.urls)),
]
