import __main__
from .nodes.http_serving import HTTPServing
NODE_CLASS_MAPPINGS["HTTPServing"] = HTTPServing
NODE_DISPLAY_NAME_MAPPINGS["HTTPServing"] = "HTTP Serving"

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
