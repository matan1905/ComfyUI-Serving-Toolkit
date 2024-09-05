import http.server
import socketserver
import json
import threading
from collections import deque

class HTTPServingHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        self.server.data_queue.append(data)
        self.server.data_ready.set()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received"}).encode('utf-8'))

class HTTPServing:
    def __init__(self):
        self.data_ready = threading.Event()
        self.data_queue = deque()
        self.http_running = False
        self.port = None
        self.handler = None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "port": ("INT", {"default": 8000, "min": 1, "max": 65535}),
            }
        }

    RETURN_TYPES = ("SERVING_CONFIG",)
    FUNCTION = "serve"
    CATEGORY = "Serving-Toolkit"

    def http_runner(self):
        with socketserver.TCPServer(("", self.port), self.handler) as httpd:
            print(f"Serving at port {self.port}")
            httpd.serve_forever()

    def serve(self, port):
        if not self.http_running:
            self.port = port
            self.handler = type('CustomHandler', (HTTPServingHandler,), {'server': self})
            threading.Thread(target=self.http_runner, daemon=True).start()
            print(f"HTTP Server running on port {self.port}")
            self.http_running = True

        if not self.data_queue:
            self.data_ready.wait()
        data = self.data_queue.popleft()
        self.data_ready.clear()

        def serve_image_function(image, frame_duration):
            # Implementation for serving image
            pass

        def serve_multi_image_function(images):
            # Implementation for serving multiple images
            pass

        def serve_text_function(text):
            # Implementation for serving text
            pass

        data["serve_image_function"] = serve_image_function
        data["serve_multi_image_function"] = serve_multi_image_function
        data["serve_text_function"] = serve_text_function

        return (data,)