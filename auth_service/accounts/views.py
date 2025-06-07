# auth/views.py
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserDetailView(APIView):
    permission_classes = [AllowAny]  # hoặc IsAuthenticated nếu cần bảo vệ

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            return Response(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": getattr(user, "role", None),
                }
            )
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Được gán từ JWT token
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()  # Lấy toàn bộ người dùng
    serializer_class = UserSerializer  # Serializer cho User

    @action(detail=False, methods=["get"])
    def get_users_by_role(self, request):
        role = request.query_params.get("role", None)
        if role:
            if role not in ["CUSTOMER", "LIBRARIAN", "ADMIN"]:
                return Response({"error": "Role không hợp lệ"}, status=400)
            users = User.objects.filter(role=role)
        else:
            users = User.objects.all()

        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
