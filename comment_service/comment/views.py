from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Comment
from .serializers import CommentSerializer
import requests
from rest_framework import status


def update_product_score(book_id):
    comments = Comment.objects.filter(book_id=book_id)

    total_confidence = 0.0
    for c in comments:
        if c.confidence is not None:
            if c.sentiment == "Tích cực":
                total_confidence += c.confidence
            elif c.sentiment == "Tiêu cực":
                total_confidence -= c.confidence
            # Trung tính thì không làm gì

    url = f"http://localhost:8002/api/book/books/{book_id}/update-score/"

    try:
        requests.post(url, json={"score": total_confidence})
    except requests.exceptions.RequestException:
        pass  # không ảnh hưởng đến việc tạo comment


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        data = self.request.data
        content = data.get("content", "")
        sentiment = None
        confidence = None

        if content:
            try:
                response = requests.post(
                    "http://localhost:8004/api/sentiment/analyze/",
                    json={"text": content},
                    timeout=3,
                )
                if response.status_code == 200:
                    result = response.json()
                    sentiment = result.get("sentiment")
                    confidence = result.get("confidence")
            except requests.exceptions.RequestException:
                pass

        comment = serializer.save(
            user_id=data.get("user_id"),
            username=data.get("username"),
            book_id=data.get("book_id"),
            content=content,
            sentiment=sentiment,
            confidence=confidence,
        )
        update_product_score(comment.book_id)

    @action(
        detail=False,
        methods=["get"],
        url_path="by-book/(?P<book_id>[^/.]+)",
    )
    def get_by_book(self, request, book_id=None):
        comments = Comment.objects.filter(book_id=book_id)
        serializer = self.get_serializer(comments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
