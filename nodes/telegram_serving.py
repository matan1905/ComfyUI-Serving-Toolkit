import telebot
from telebot import types
from collections import deque
import threading
import io
from PIL import Image
import base64
import numpy as np
import torch
from .utils import tensorToImageConversion, parse_command_string, CommandRegistry


class TelegramServing:
    def __init__(self):
        self.data_ready = threading.Event()
        self.data = deque()
        self.telegram_running = False
        self.bot = None
        self.allowed_chat_ids = None
        self.command_registry = CommandRegistry()

    def telegram_handler(self):
        @self.bot.message_handler()
        def handle_command(message):
            chat_id = str(message.chat.id)
            if self.allowed_chat_ids and chat_id not in self.allowed_chat_ids:
                print(
                    f"Allowed chatids are: {self.allowed_chat_ids}, but got message from user: {message.from_user.username}, chatid: {chat_id} ! Skipping message.")
                return  # Silently ignore messages

            command_name = message.text.split()[0][1:]  # Extract command name without '/'
            if not self.command_registry.has_command(command_name):
                return  # Silently ignore wrong commands

            print(f"Received command from {message.chat.id}: {message.text}")
            parsed_data = parse_command_string(message.text, command_name)

            async def serve_multi_image_function(images):
                media_group = []
                for i, img in enumerate(images):
                    img_np = (img.cpu().numpy() * 255).astype('uint8')
                    img_pil = Image.fromarray(img_np.squeeze())
                    img_bytes = io.BytesIO()
                    img_pil.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    media_group.append(types.InputMediaPhoto(img_bytes))

                self.bot.send_media_group(message.chat.id, media_group)

            def serve_image_function(image, frame_duration):
                image_file = tensorToImageConversion(image, frame_duration)
                self.bot.send_photo(message.chat.id, image_file)

            def is_command(command):
                return command == command_name

            parsed_data["is_command"] = is_command
            parsed_data["serve_image_function"] = serve_image_function
            parsed_data["serve_multi_image_function"] = serve_multi_image_function
            parsed_data["serve_text_function"] = lambda text: self.bot.reply_to(message, text)

            if message.document:
                file_info = self.bot.get_file(message.document.file_id)
                downloaded_file = self.bot.download_file(file_info.file_path)
                parsed_data["attachment_url_0"] = downloaded_file

            self.data.append(parsed_data)
            self.data_ready.set()

        self.bot.polling()

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
                    "multiline": False,
                    "default": ""
                }),
            },
            "optional": {
                "allowed_chat_ids": ("STRING", {
                    "multiline": True,
                    "default": ""
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

    def serve(self, telegram_token, allowed_chat_ids=""):
        self.allowed_chat_ids = allowed_chat_ids
        if not self.telegram_running:
            self.bot = telebot.TeleBot(telegram_token)
            threading.Thread(target=self.telegram_handler, daemon=True).start()
            print("Telegram bot running, listening for all commands")
            self.telegram_running = True

        data = self.get_data()
        return (data,)