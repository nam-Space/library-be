# comment/models.py
from django.db import models


class Comment(models.Model):
    user_id = models.IntegerField()
    username = models.CharField(max_length=255)
    book_id = models.IntegerField()
    content = models.TextField()
    sentiment = models.CharField(max_length=20, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)  # ← Thêm trường này
    created_at = models.DateTimeField(auto_now_add=True)
