# book/admin.py

from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "published_date", "quantity")
    search_fields = ("title", "author")
    list_filter = ("published_date",)
