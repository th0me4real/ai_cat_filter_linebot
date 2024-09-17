# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden,JsonResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
from io import BytesIO

# 載入模型
model = load_model('./ml/cat_classifier_model.h5', compile=False)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# 圖片預處理函數
def preprocess_image(image):
    img = image.resize((150, 150))  # 調整為模型要求的尺寸
    img = np.array(img) / 255.0     # 將像素值縮放到 [0, 1] 之間
    img = np.expand_dims(img, axis=0)  # 增加一個維度，變成 (1, 150, 150, 3)
    return img

# LINE Bot 設定（從 settings.py 中讀取）
from django.conf import settings
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def callback(request):
    signature = request.META.get('HTTP_X_LINE_SIGNATURE', '')
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HttpResponseForbidden()
    return HttpResponse('OK')

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # 獲取圖片內容
    message_content = line_bot_api.get_message_content(event.message.id)
    image = Image.open(BytesIO(message_content.content))

    # 預處理圖片
    preprocessed_image = preprocess_image(image)

    # 模型預測
    prediction = model.predict(preprocessed_image)
    result = "這是一隻狗!" if prediction[0][0] > 0.5 else "這是一隻貓!"

    # 回應用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )
    
