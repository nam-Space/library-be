# auth/urls.py
from django.urls import path, include
from .views import RegisterView, UserDetailView, UserProfileView, UserViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"accounts", UserViewSet)  # Đăng ký viewset của User

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", UserProfileView.as_view(), name="get-profile"),
    path(
        "users/role/",
        UserViewSet.as_view({"get": "get_users_by_role"}),
        name="get_users_by_role",
    ),
    path("<int:pk>/", UserDetailView.as_view(), name="user_detail"),
]
