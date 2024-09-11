import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque
import json
import base64
from io import BytesIO
from .utils import tensorToImageConversion
from PIL import Image


class HTTPServing:
    def __init__(self):
        self.enable_cross_origin_requests = None
        self.data_ready = threading.Event()
        self.data = deque()
        self.http_running = False
        self.port = None
        self.server = None
        self.output_ready = threading.Event()
        self.output = None

    def http_handler(self):
        class RequestHandler(BaseHTTPRequestHandler):
            def do_OPTIONS(self2):
                if(self.enable_cross_origin_requests):
                    self2.send_response(200)
                    self2.send_header('Access-Control-Allow-Origin', '*')
                    self2.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self2.send_header('Access-Control-Allow-Headers', '*')
                    self2.end_headers()


            def do_POST(self2):
                content_length = int(self2.headers['Content-Length'])
                post_data = self2.rfile.read(content_length)
        data = {}
        form_data = post_data.decode('utf-8').split('&')
        for item in form_data:
            key, value = item.split('=')
            data[key] = value.replace('+', ' ')
                self.data.append(data)
                self.data_ready.set()

                self.output_ready.wait()
                self.output_ready.clear()
                response = self.output
                self2.send_response(200)
                self2.send_header('Content-type', 'application/json')
                # Cors
                if(self.enable_cross_origin_requests):
                    self2.send_header('Access-Control-Allow-Origin', '*')
                    self2.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self2.send_header('Access-Control-Allow-Headers', '*')

                self2.end_headers()
                self2.wfile.write(json.dumps(response).encode('utf-8'))




            def do_GET(self2):
                if self2.path == '/':
                    self2.send_response(200)
                    self2.send_header('Content-type', 'text/html')
                    self2.end_headers()
            html_form = """
            <html>
            <body>
            <h2>ComfyUI HTTP Serving</h2>
            <form method="post">
                <label for="prompt">Prompt:</label><br>
                <textarea name="prompt" rows="4" cols="50"></textarea><br>
                <label for="negative_prompt">Negative Prompt:</label><br>
                <textarea name="negative_prompt" rows="4" cols="50"></textarea><br>
                <input type="submit" value="Generate">
            </form>
            </body>
            </html>
            """
            self2.wfile.write(html_form.encode('utf-8'))

        self.server = HTTPServer(('', self.port), RequestHandler)
        print(f"HTTP Server running on port {self.port}")
        self.server.serve_forever()

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
                "port": ("INT", {"default": 8000, "min": 1, "max": 65535}),
                "enable_cross_origin_requests": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("SERVING_CONFIG",)
    RETURN_NAMES = ("Serving config",)
    FUNCTION = "serve"
    CATEGORY = "Serving-Toolkit"
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def serve(self, port,enable_cross_origin_requests):
        self.enable_cross_origin_requests = enable_cross_origin_requests

        if not self.http_running:
            self.port = port
            threading.Thread(target=self.http_handler, daemon=True).start()
            print(f"HTTP Server running on port {port}")
            self.http_running = True

        self.output_ready.clear() # Prevent deadlock if failed in previous run
        data = self.get_data()

        def serve_multi_image_function(images):
            base64_images = []
            for img in images:
                img_np = (img.cpu().numpy() * 255).astype('uint8')
                img_bytes = BytesIO()
                Image.fromarray(img_np.squeeze()).save(img_bytes, format='PNG')
                base64_img = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                base64_images.append(base64_img)
            response = {
                "base64_images": base64_images,
            }
            self.output = response
            self.output_ready.set()


        def serve_image_function(image, frame_duration):
            image_file = tensorToImageConversion(image, frame_duration)
            base64_img = base64.b64encode(image_file.read()).decode('utf-8')
            response = {
                "base64_img": base64_img,
            }
            self.output = response
            self.output_ready.set()

        def serve_text_function(text):
            response = {
                "text": text,
            }
            self.output = response
            self.output_ready.set()

        data["serve_image_function"] = serve_image_function
        data["serve_multi_image_function"] = serve_multi_image_function
        data["serve_text_function"] = serve_text_function

        return (data,)
