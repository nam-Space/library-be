# borrow/models.py

from django.db import models


class BorrowRecord(models.Model):
    user_id = models.IntegerField()
    username = models.CharField(max_length=150, blank=True)  # ✅ thêm
    book_id = models.IntegerField()
    book_title = models.CharField(max_length=255, blank=True)  # ✅ thêm
    quantity = models.PositiveIntegerField(default=1)
    borrowed_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"User {self.user_id} mượn Book {self.book_id}"
