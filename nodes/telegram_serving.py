import threading
from collections import deque
import json
import base64
from io import BytesIO
from .utils import tensorToImageConversion, parse_command_string
import asyncio
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

class TelegramServing:
    telegram_running = False

    def __init__(self):
        self.registered_command = False
        self.data_ready = threading.Event()
        self.data = deque()
        self.telegram_token = None
        self.application = None

    def telegram_runner(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.application.run_polling()

    def get_data(self):
        if not self.data:
            self.data_ready.wait()
        data = self.data.popleft()
        self.data_ready.clear()
        return data

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "telegram_token": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "command_name": ("STRING", {
                    "multiline": False,
                    "default": "generate"
                })
            }
        }

    RETURN_TYPES = ("SERVING_CONFIG",)
    RETURN_NAMES = ("Serving config",)
    FUNCTION = "serve"
    CATEGORY = "Serving-Toolkit"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    async def execute(self, update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
        parsed_data = parse_command_string(update.message.text, self.command_name)

        async def serve_multi_image_function(images):
            for i, img in enumerate(images):
                try:
                    img_np = (img.cpu().numpy() * 255).astype('uint8')
                    img_bytes = BytesIO()
                    Image.fromarray(img_np.squeeze()).save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    await update.message.reply_photo(photo=img_bytes)
                except Exception as e:
                    print(f"Error processing image {i + 1}: {str(e)}")

        def serve_image_function(image, frame_duration):
            image_file = tensorToImageConversion(image, frame_duration)
            asyncio.run_coroutine_threadsafe(
                update.message.reply_document(document=image_file, filename='image.webp'),
                self.application.loop
            )

        parsed_data["serve_image_function"] = serve_image_function
        parsed_data["serve_multi_image_function"] = serve_multi_image_function
        parsed_data["serve_text_function"] = lambda text: asyncio.run_coroutine_threadsafe(
            update.message.reply_text(text=text), self.application.loop)

        if update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
            parsed_data["attachment_url_0"] = file.file_path

        self.data.append(parsed_data)
        self.data_ready.set()

    def serve(self, command_name, telegram_token):
        if not TelegramServing.telegram_running:
            self.telegram_token = telegram_token
            self.command_name = command_name
            self.application = ApplicationBuilder().token(self.telegram_token).build()
            
            if not self.registered_command:
                self.registered_command = True
                self.application.add_handler(CommandHandler(command_name, self.execute))
            
            run_telegram = threading.Thread(target=self.telegram_runner)
            run_telegram.start()
            print("Telegram Client running")
            TelegramServing.telegram_running = True

        data = self.get_data()
        return (data,)