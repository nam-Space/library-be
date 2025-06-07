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
        book_price = book_data.get("price", 0.0)
        img_url = book_data.get("image", "")  # ✅ thêm dòng này
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            username=username,
            book_title=book_title,
            price=book_price,  # ✅ thêm đơn giá
            img_url=img_url,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Đây là hàm cập nhật cho LIBRARIAN, ADMIN để trả lại sách về giá trị ban đầu nếu người dùng trả sách thành công hoặc trả muộn
    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        record = self.get_object()

        # Nếu sách đã được trả
        if record.status == "returned":
            return Response({"message": "Sách đã trả trước đó."})

        # Lấy thông tin từ request để cập nhật status, punish và note
        new_status = request.data.get(
            "status", "returned"
        )  # Nếu không có status, mặc định là "returned"
        new_punish = request.data.get("punish", 0.0)  # Tiền phạt
        new_note = request.data.get("note", "")  # Ghi chú

        # Gọi book_service để cộng lại tồn kho
        book_url = f"{BOOK_SERVICE_URL}{record.book_id}/"
        book_res = requests.get(book_url)
        if book_res.status_code != 200:
            return Response({"error": "Không lấy được sách"}, status=500)

        book_data = book_res.json()
        book_data["quantity"] += record.quantity  # Cộng lại số sách vào kho
        update_res = requests.put(book_url, json=book_data)
        if update_res.status_code not in (200, 202):
            return Response({"error": "Không thể cập nhật tồn kho"}, status=500)

        # Cập nhật các thông tin khác vào BorrowRecord
        record.returned = True
        record.return_date = date.today()  # Cập nhật ngày trả sách
        record.status = new_status  # Cập nhật status
        record.punish = new_punish  # Cập nhật tiền phạt
        record.note = new_note  # Cập nhật ghi chú

        # Lưu bản ghi
        record.save()

        return Response({"message": "✅ Trả sách thành công!"})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Lấy các giá trị cũ của các trường (số lượng sách, book_id)
        original_quantity = instance.quantity
        original_book_id = instance.book_id

        # Lấy serializer và kiểm tra tính hợp lệ của dữ liệu request
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Lấy giá trị mới từ dữ liệu request
        new_quantity = serializer.validated_data.get("quantity", original_quantity)
        new_book_id = serializer.validated_data.get("book_id", original_book_id)
        new_status = serializer.validated_data.get("status", instance.status)
        new_punish = serializer.validated_data.get("punish", instance.punish)
        new_due_date = serializer.validated_data.get("due_date", instance.due_date)
        new_note = serializer.validated_data.get("note", instance.note)
        new_returned = serializer.validated_data.get("returned", instance.returned)
        new_return_date = serializer.validated_data.get(
            "return_date", instance.return_date
        )

        delta = new_quantity - original_quantity  # Tính thay đổi số lượng sách

        # Gọi book_service để cập nhật tồn kho
        book_url = f"{BOOK_SERVICE_URL}{new_book_id}/"
        book_res = requests.get(book_url)
        if book_res.status_code != 200:
            return Response({"error": "Không lấy được sách"}, status=500)

        book_data = book_res.json()
        book_data["quantity"] -= delta  # Cập nhật tồn kho
        if book_data["quantity"] < 0:
            return Response({"error": "Không đủ sách tồn"}, status=400)

        update_res = requests.put(book_url, json=book_data)
        if update_res.status_code not in (200, 202):
            return Response({"error": "Không thể cập nhật kho"}, status=500)

        # Lấy lại title, price, và img_url nếu book_id thay đổi
        book_title = book_data.get("title", instance.book_title)
        book_price = book_data.get("price", instance.price)
        img_url = book_data.get("image", instance.img_url)

        # Cập nhật các trường mới trong bản ghi
        serializer.save(
            book_title=book_title,
            price=book_price,
            img_url=img_url,
            status=new_status,
            punish=new_punish,
            due_date=new_due_date,
            note=new_note,
            returned=new_returned,
            return_date=new_return_date,
        )

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
            serializer = self.get_serializer(records, many=True)

            return Response(serializer.data)

        serializer = self.get_serializer(records, many=True)

        return Response(serializer.data)

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
