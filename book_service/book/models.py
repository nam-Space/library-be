# book/models.py

from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField()
    published_date = models.DateField()
    quantity = models.IntegerField(default=0)
    image = models.URLField(blank=True)

    def __str__(self):
        return self.title
