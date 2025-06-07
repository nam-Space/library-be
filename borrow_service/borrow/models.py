from django.db import models


class BorrowRecord(models.Model):
    user_id = models.IntegerField()
    username = models.CharField(max_length=150, blank=True)
    book_id = models.IntegerField()
    book_title = models.CharField(max_length=255, blank=True)
    img_url = models.URLField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    borrowed_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    # ✅ Thêm trường due_date
    due_date = models.DateField(null=True, blank=True)

    # ✅ Thêm trường status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Chờ duyệt"),
            ("returned", "Đã trả"),
            ("overdue", "Quá hạn"),
            ("failed", "Từ chối"),
        ],
        default="pending",
    )

    # ✅ Thêm trường punish (tiền phạt)
    punish = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # ✅ Thêm trường note
    note = models.TextField(blank=True, null=True)  # Trường ghi chú, có thể để trống

    def __str__(self):
        return f"User {self.user_id} mượn Book {self.book_id}"
