from .nodes.http_serving import HTTPServing
from .nodes.all_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .nodes.telegram_serving import TelegramServing
NODE_CLASS_MAPPINGS["TelegramServing"] = TelegramServing
NODE_DISPLAY_NAME_MAPPINGS["TelegramServing"] = "Telegram Serving"


NODE_CLASS_MAPPINGS["HTTPServing"] = HTTPServing
NODE_DISPLAY_NAME_MAPPINGS["HTTPServing"] = "HTTP Serving"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
