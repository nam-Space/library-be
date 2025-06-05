# borrow/views.py
from rest_framework.decorators import action
import requests
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import BorrowRecord
from .serializers import BorrowRecordSerializer
from django.db.models import Sum, Count
from datetime import date


AUTH_SERVICE_URL = "http://localhost:8001/api/account/"
BOOK_SERVICE_URL = "http://localhost:8002/api/book/books/"


class BorrowRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        book_id = request.data.get("book_id")
        quantity = int(request.data.get("quantity", 1))

        # Lấy thông tin sách
        book_url = f"{BOOK_SERVICE_URL}{book_id}/"
        book_res = requests.get(book_url)
        if book_res.status_code != 200:
            return Response({"error": "Không tìm thấy sách"}, status=404)

        book_data = book_res.json()
        available_quantity = book_data["quantity"]

        if quantity > available_quantity:
            return Response({"error": "Không đủ sách để mượn"}, status=400)

        # Trừ kho
        book_data["quantity"] = available_quantity - quantity
        update_res = requests.put(book_url, json=book_data)
        if update_res.status_code not in (200, 202):
            return Response({"error": "Không thể cập nhật kho sách"}, status=500)

        # Lấy thông tin user
        user_url = f"{AUTH_SERVICE_URL}{user_id}/"
        user_res = requests.get(user_url)
        username = "Unknown"
        if user_res.status_code == 200:
            username = user_res.json().get("username", "Unknown")

        # Lưu bản ghi mượn
        book_title = book_data.get("title", "Unknown")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(username=username, book_title=book_title)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        record = self.get_object()
        if record.returned:
            return Response({"message": "Sách đã trả trước đó."})

        # Gọi book_service để cộng lại tồn kho
        book_url = f"{BOOK_SERVICE_URL}{record.book_id}/"
        book_res = requests.get(book_url)
        if book_res.status_code != 200:
            return Response({"error": "Không lấy được sách"}, status=500)

        book_data = book_res.json()
        book_data["quantity"] += record.quantity
        update_res = requests.put(book_url, json=book_data)
        if update_res.status_code not in (200, 202):
            return Response({"error": "Không thể cập nhật tồn kho"}, status=500)

        record.returned = True
        record.return_date = date.today()
        record.save()

        return Response({"message": "✅ Trả sách thành công!"})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        original_quantity = instance.quantity
        original_book_id = instance.book_id

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        new_quantity = serializer.validated_data.get("quantity", original_quantity)
        new_book_id = serializer.validated_data.get("book_id", original_book_id)

        delta = new_quantity - original_quantity

        # Nếu số lượng thay đổi → trừ/cộng kho
        book_url = f"{BOOK_SERVICE_URL}{new_book_id}/"
        book_res = requests.get(book_url)
        if book_res.status_code != 200:
            return Response({"error": "Không lấy được sách"}, status=500)

        book_data = book_res.json()
        book_data["quantity"] -= delta
        if book_data["quantity"] < 0:
            return Response({"error": "Không đủ sách tồn"}, status=400)

        update_res = requests.put(book_url, json=book_data)
        if update_res.status_code not in (200, 202):
            return Response({"error": "Không thể cập nhật kho"}, status=500)

        # Nếu book_id thay đổi thì lấy lại book_title
        book_title = book_data.get("title", instance.book_title)

        # Cập nhật bản ghi
        serializer.save(book_title=book_title)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Nếu sách chưa trả thì cộng lại vào kho
        if not instance.returned:
            book_url = f"{BOOK_SERVICE_URL}{instance.book_id}/"
            book_res = requests.get(book_url)

            if book_res.status_code != 200:
                return Response({"error": "Không tìm được sách"}, status=500)

            book_data = book_res.json()
            book_data["quantity"] += instance.quantity

            update_res = requests.put(book_url, json=book_data)
            if update_res.status_code not in (200, 202):
                return Response(
                    {"error": "Không thể cập nhật lại kho sách"}, status=500
                )

        # Xoá bản ghi mượn
        self.perform_destroy(instance)
        return Response({"message": "✅ Xoá bản ghi mượn thành công."}, status=204)

    @action(detail=False, methods=["get"], url_path="statistic-full")
    def statistic_full(self, request):
        returned = request.query_params.get("returned")
        records = BorrowRecord.objects.all()
        if returned in ["true", "false"]:
            records = records.filter(returned=(returned.lower() == "true"))
        result = []

        for record in records:

            result.append(
                {
                    "id": record.id,
                    "user_id": record.user_id,
                    "username": record.username,
                    "book_id": record.book_id,
                    "book_title": record.book_title,
                    "quantity": record.quantity,
                    "borrowed_date": record.borrowed_date,
                    "return_date": record.return_date,
                    "returned": record.returned,
                }
            )

        return Response(result)

    @action(detail=False, methods=["get"], url_path="history")
    def history_by_user(self, request):
        user_id = request.query_params.get("user_id")
        returned = request.query_params.get("returned")  # optional

        if not user_id:
            return Response({"error": "Thiếu user_id"}, status=400)

        records = BorrowRecord.objects.filter(user_id=user_id)

        if returned is not None:
            if returned.lower() == "true":
                records = records.filter(returned=True)
            elif returned.lower() == "false":
                records = records.filter(returned=False)

        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
