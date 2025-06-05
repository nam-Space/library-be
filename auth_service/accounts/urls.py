# auth/urls.py
from django.urls import path
from .views import RegisterView, UserDetailView, UserProfileView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", UserProfileView.as_view(), name="get-profile"),
    path("<int:pk>/", UserDetailView.as_view(), name="user_detail"),
]
