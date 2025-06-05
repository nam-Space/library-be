# book/views.py

from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_queryset(self):
        queryset = Book.objects.all()
        keyword = self.request.query_params.get("keyword", "").strip()

        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | Q(author__icontains=keyword)
            )

        return queryset
