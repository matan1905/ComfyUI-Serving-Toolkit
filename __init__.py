from .nodes.http_serving import HTTPServing
from .nodes.all_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


NODE_CLASS_MAPPINGS["HTTPServing"] = HTTPServing
NODE_DISPLAY_NAME_MAPPINGS["HTTPServing"] = "HTTP Serving"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
