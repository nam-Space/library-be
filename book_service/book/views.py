# book/views.py

from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from rest_framework import status
from decimal import Decimal


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_queryset(self):
        queryset = Book.objects.all().order_by("-score")
        keyword = self.request.query_params.get("keyword", "").strip()

        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | Q(author__icontains=keyword)
            )

        return queryset

    @action(detail=True, methods=["post"], url_path="update-score")
    def update_score(self, request, pk=None):
        try:
            # Lấy đối tượng sách từ DB
            book = self.get_object()
            score = request.data.get("score")

            # Kiểm tra nếu không có score trong request
            if score is None:
                return Response(
                    {"error": "Missing 'score'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            book.price = Decimal(str(book.price))
            book.score = Decimal(str(score))

            # Lưu bản ghi sau khi cập nhật
            book.save()

            # Trả về phản hồi với thông tin đã cập nhật
            return Response(
                {"success": True, "score": book.score},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
