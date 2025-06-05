from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("CUSTOMER", "Customer"),
        ("LIBRARIAN", "Librarian"),
        ("ADMIN", "Admin"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="CUSTOMER")

    def __str__(self):
        return f"{self.username} ({self.role})"


class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer_profile"
    )
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Customer: {self.user.username}"


class Librarian(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="librarian_profile"
    )
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Librarian: {self.user.username}"
