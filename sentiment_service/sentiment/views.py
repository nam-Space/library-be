import joblib
import numpy as np
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import os

# Load tokenizer & models 1 lần khi khởi động
TOKENIZER = joblib.load("tokenizer1.pkl")
LSTM_MODEL = load_model("lstm_model.h5")

MAX_LEN = 40

LABELS = {0: "Tiêu cực", 1: "Trung tính", 2: "Tích cực"}


class PredictSentimentView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "Missing text"}, status=400)

        # Tiền xử lý văn bản
        sequences = TOKENIZER.texts_to_sequences([text])
        padded = pad_sequences(sequences, maxlen=MAX_LEN)

        # Dự đoán
        probs = LSTM_MODEL.predict(padded)
        predicted_label = np.argmax(probs)

        return Response(
            {
                "input": text,
                "sentiment": LABELS[predicted_label],
                "confidence": float(np.max(probs)),
            }
        )
