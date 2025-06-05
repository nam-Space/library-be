from rest_framework import serializers
from .models import User, Customer, Librarian


class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "password", "email", "role")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        role = validated_data.pop("role")
        user = User.objects.create_user(**validated_data, role=role)

        if role == "CUSTOMER":
            Customer.objects.create(user=user)
        elif role == "LIBRARIAN":
            Librarian.objects.create(user=user)

        return user
