import time
import threading
from .discord_client import discord_client
from collections import deque
from .utils import parse_command_string, tensorToImageConversion, CommandRegistry
import discord
import asyncio
import requests
import io
import base64
from PIL import Image
import numpy as np
import websocket
import json
import torch
import torchvision.transforms as transforms
import cv2
import nodes



class ServingOutput:
    def __init__(self):
        # start listening to api/discord
        # when something happen, pass to serving manager with the details
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "image": ("IMAGE",),
                "frame_duration": ("INT", {"default": 30, "min": 1, "step": 1, "max": 9999999}),
            },
            "optional": {
                "chained_execution": ("SHOULD_EXECUTE",),
            }
}

    RETURN_TYPES = ("SHOULD_EXECUTE",)
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "out"

    # OUTPUT_NODE = True

    CATEGORY = "Serving-Toolkit"

    def out(self, image,serving_config,frame_duration, chained_execution=None):
        serving_config["serve_image_function"](image,frame_duration)
        return ({}, )



class ServingTextOutput:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "text": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "chained_execution": ("SHOULD_EXECUTE",),
            }
        }

    RETURN_TYPES = ("SHOULD_EXECUTE",)
    FUNCTION = "out"
    # OUTPUT_NODE = True
    CATEGORY = "Serving-Toolkit"

    def out(self, serving_config, text, chained_execution=None):
        if "serve_text_function" in serving_config:
            serving_config["serve_text_function"](text)
        else:
            print("Warning: serve_text_function not found in serving_config")
        return ({}, )


class ServingInputText:
    def __init__(self):
        # start listening to api/discord
        # when something happen, pass to serving manager with the details
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "argument": ("STRING", {
                    "multiline": False,
                    "default": "prompt"
                }),
                "default": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)

    FUNCTION = "out"

    CATEGORY = "Serving-Toolkit"

    def out(self, serving_config, argument,default):
        if argument not in serving_config:
            return (default,)
        return (serving_config[argument],)

class ServingInputTextImage:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "argument": ("STRING", {
                    "multiline": False,
                    "default": "prompt"
                }),
                "default_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
            },
            "optional":{
                "default_image": ("IMAGE",)
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE",)
    FUNCTION = "out"
    CATEGORY = "Serving-Toolkit"

    def convert_color(self, image):
        if len(image.shape) > 2 and image.shape[2] >= 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def load_image(self, base64_str):
        nparr = np.frombuffer(base64.b64decode(base64_str), np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        result = self.convert_color(result)
        result = result.astype(np.float32) / 255.0
        image = torch.from_numpy(result)[None,]
        return image

    def out(self, serving_config, argument, default_prompt, default_image = None):
        attachment_url_key = "attachment_url_0"
        if attachment_url_key not in serving_config:
            if default_image is not None:
                return (default_image,)
            serving_config["serve_text_function"]("This command requires an image")
            nodes.interrupt_processing(True)
            return ('', None)

        attachment_url = serving_config[attachment_url_key]
        response = requests.get(attachment_url)
        image = Image.open(io.BytesIO(response.content)).convert("RGB")

        # Convert PIL image to base64 string
        image_file = io.BytesIO()
        image.save(image_file, format='PNG')
        image_file.seek(0)
        base64_img = base64.b64encode(image_file.read()).decode('utf-8')

        # Use the base64 string to get the image tensor
        img_out = self.load_image(base64_img)
        if argument not in serving_config:
            return (default_prompt, img_out)
        return (serving_config[argument], img_out)


class ServingInputNumber:
    def __init__(self):
        # start listening to api/discord
        # when something happen, pass to serving manager with the details
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "argument": ("STRING", {
                    "multiline": False,
                    "default": "number"
                }),
                "default": ("FLOAT", {"default": 0.0, "min": -999999.0, "max": 999999.0, "step": 0.0001}),
                "min_value": ("FLOAT", {"default": -999999.0, "min": -999999.0, "max": 999999.0, "step": 0.0001}),
                "max_value": ("FLOAT", {"default": 999999.0, "min": -999999.0, "max": 999999.0, "step": 0.0001}),
                "step": ("FLOAT", {"default": 0.1, "min": -999999.0, "max": 999999.0, "step": 0.0001}),
            }
        }

    RETURN_TYPES = ("FLOAT", "INT", "STRING")
    RETURN_NAMES = ("float_value", "int_value", "number_text")

    FUNCTION = "out"

    CATEGORY = "Serving-Toolkit"

    def out(self, serving_config, argument,default, min_value, max_value, step):
        val = default
        if argument in serving_config and serving_config[argument].replace('.','',1).isdigit():
            val = serving_config[argument]
        valFloat = min(max(float(val), min_value), max_value) // step * step
        valInt = round(valFloat)
        number_text = str(valFloat)
        return (valFloat, valInt, number_text)


class ServingMultiImageOutput:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "images": ("IMAGE",),
            },
            "optional": {
                "chained_execution": ("SHOULD_EXECUTE",),
            }
        }

    RETURN_TYPES = ("SHOULD_EXECUTE",)
    FUNCTION = "out"
    # OUTPUT_NODE = True
    CATEGORY = "Serving-Toolkit"

    def out(self, serving_config, images, chained_execution=None):
        if "serve_multi_image_function" in serving_config:
            serve_func = serving_config["serve_multi_image_function"]
            if asyncio.iscoroutinefunction(serve_func):
                future = asyncio.run_coroutine_threadsafe(serve_func(images), discord_client.loop)
                try:
                    future.result(timeout=60)  # Wait for up to 60 seconds
                except Exception as e:
                    print(f"Error sending images: {str(e)}")
            else:
                serve_func(images)
        else:
            print("Warning: serve_multi_image_function not found in serving_config")
        return ({}, )

class DiscordServing():
    discord_running = False
    def __init__(self):
        self.registered_command = False
        self.data_ready = threading.Event()
        self.data = deque()
        self.discord_token = None
        self.command_registry = CommandRegistry()

    def discord_runner(self):
         discord_client.run(self.discord_token)

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
                "discord_token": ("STRING", {
                    "multiline": True,
                    "default": ""
                })
            }
        }

    RETURN_TYPES = ("SERVING_CONFIG",)
    RETURN_NAMES = ("Serving config",)

    FUNCTION = "serve"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    CATEGORY = "Serving-Toolkit"

    def serve(self, discord_token):
        if not DiscordServing.discord_running:
            self.discord_token = discord_token
            run_discord = threading.Thread(target=self.discord_runner)
            run_discord.start()
            print("Client running")
            DiscordServing.discord_running = True
        if not self.registered_command:
            self.registered_command = True
            @discord_client.event
            async def on_message(message):
                if message.content.startswith('!'):
                    command_name = message.content.split()[0][1:]

                    if not self.command_registry.has_command(command_name):
                        return

                    parsed_data = parse_command_string(message.content, command_name)

                    async def serve_multi_image_function(images):
                        discord_files = []
                        for i, img in enumerate(images):
                            try:
                                if isinstance(img, np.ndarray):
                                    img_np = img
                                else:
                                    img_np = img.cpu().numpy()

                                if img_np.dtype != np.uint8:
                                    img_np = (img_np * 255).astype(np.uint8)

                                if len(img_np.shape) == 2:
                                    img_np = np.stack([img_np] * 3, axis=-1)
                                elif len(img_np.shape) == 3 and img_np.shape[2] == 1:
                                    img_np = np.concatenate([img_np] * 3, axis=2)
                                elif img_np.shape[2] == 4:
                                    img_np = img_np[:, :, :3]

                                img_pil = Image.fromarray(img_np)
                                img_bytes = io.BytesIO()
                                img_pil.save(img_bytes, format='PNG')
                                img_bytes.seek(0)
                                discord_files.append(discord.File(img_bytes, filename=f'image_{i}.png'))
                            except Exception as e:
                                print(f"Error processing image {i + 1}: {str(e)}")

                        try:
                            print("Attempting to send images...")
                            await message.reply(files=discord_files)
                            print("Images sent successfully")
                        except Exception as e:
                            print(f"Error sending images: {str(e)}")

                    def serve_image_function(image, frame_duration):
                        image_file = tensorToImageConversion(image, frame_duration)
                        asyncio.run_coroutine_threadsafe(message.reply(file=discord.File(image_file, filename='image.webp')), discord_client.loop)

                    def is_command(command):
                        return bool(command_name == command)

                    parsed_data["serve_image_function"] = serve_image_function
                    parsed_data["serve_multi_image_function"] = serve_multi_image_function
                    parsed_data["is_command"] = is_command
                    parsed_data["serve_text_function"] = lambda text: asyncio.run_coroutine_threadsafe(
                        message.reply(content=text), discord_client.loop)
                    parsed_data.update({f"attachment_url_{i}": attachment.url for i, attachment in enumerate(message.attachments)})
                    self.data.append(parsed_data)
                    self.data_ready.set()

        data = self.get_data()

        return (data,)
class WebSocketServing():
    def __init__(self):
        self.data_ready = threading.Event()
        self.data = deque()
        self.ws_running = False
        self.websocket_url= None
        self.ws = None
        self.command_registry = CommandRegistry()
        pass
    def on_message(self,ws,message):
        try:
            parsed = json.loads(message)
            if "command_name" in parsed and not self.command_registry.has_command(parsed["command_name"]):
                return
            self.data.append(parsed)
            self.data_ready.set()
        except Exception as e:
            print("Error parsing JSON", e)
        

    def on_close(self,ws):
        print("WS Client closed!")

    def on_error(self,ws,error):
        print("WS Client error: ", error)
        # Try to reconnect
        time.sleep(1)
        self.ws_runner()

    def ws_runner(self):
        print("Starting WS Client...")
        self.ws = websocket.WebSocketApp( self.websocket_url,
                                         
                              on_message=self.on_message, on_close= self.on_close, on_error=self.on_error)
        while True:
            try:
                self.ws.run_forever(reconnect=1,
                                    ping_interval=10,
                                    ping_timeout=5,)
            except Exception as e:
                print("WS Client error: ", e)
                time.sleep(5)
                continue
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
                "websocket_url": ("STRING", {
                    "multiline": False,
                    "default": ""
                })
            }
        }

    RETURN_TYPES = ("SERVING_CONFIG",)
    RETURN_NAMES = ("Serving config",)

    FUNCTION = "serve"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")
    # OUTPUT_NODE = False

    CATEGORY = "Serving-Toolkit"

    def serve(self, websocket_url):
        if not self.ws_running:
            self.websocket_url = websocket_url
            threading.Thread(target=self.ws_runner).start()
            print("WS Client running")
            self.ws_running = True

        data = self.get_data()
        def serve_multi_image_function(images):
            base64_images = []
            for img in images:
                img_np = (img.cpu().numpy() * 255).astype(np.uint8)
                if len(img_np.shape) == 3:
                    img_np = np.expand_dims(img_np, axis=-1)
                if img_np.shape[-1] == 4:
                    img_np = img_np[:,:,:3]
                img_pil = Image.fromarray(img_np.squeeze(), 'RGB')
                img_bytes = io.BytesIO()
                img_pil.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                base64_img = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                base64_images.append(base64_img)
            response = {
                "base64_images": base64_images,
                "_requestId": data["_requestId"]
            }
            self.ws.send(json.dumps(response))

        def serve_image_function(image, frame_duration):
                    image_file = tensorToImageConversion(image, frame_duration)
                    base64_img = base64.b64encode(image_file.read()).decode('utf-8')
                    response= {
                        "base64_img":base64_img,
                        "_requestId":data["_requestId"] # It's assumed that it will exist.
                    }
                    self.ws.send(json.dumps(response))

        def is_command(command):
            return bool(data["command_name"] == command)

        data["serve_image_function"] = serve_image_function
        data["serve_multi_image_function"] = serve_multi_image_function
        data["serve_text_function"] = lambda text: self.ws.send(
            json.dumps({"text": text, "_requestId": data["_requestId"]}))
        data["is_command"] = is_command

        return (data,)

class ServingInputImage:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),

            },
            "optional":{
                "default_image": ("IMAGE",)
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "out"
    CATEGORY = "Serving-Toolkit"

    def convert_color(self, image):
        if len(image.shape) > 2 and image.shape[2] >= 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def load_image(self, base64_str):
        nparr = np.frombuffer(base64.b64decode(base64_str), np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        result = self.convert_color(result)
        result = result.astype(np.float32) / 255.0
        image = torch.from_numpy(result)[None,]
        return image

    def out(self, serving_config, default_image = None):
        attachment_url_key = "attachment_url_0"
        if attachment_url_key not in serving_config:
            if default_image is not None:
                return (default_image,)
            serving_config["serve_text_function"]("This command requires an image")
            nodes.interrupt_processing(True)
            return (None,)

        attachment_url = serving_config[attachment_url_key]
        response = requests.get(attachment_url)
        image = Image.open(io.BytesIO(response.content)).convert("RGB")

        # Convert PIL image to base64 string
        image_file = io.BytesIO()
        image.save(image_file, format='PNG')
        image_file.seek(0)
        base64_img = base64.b64encode(image_file.read()).decode('utf-8')

        # Use the base64 string to get the image tensor
        return (self.load_image(base64_img),)


class ServingInputImageAsLatent:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG",),
                "vae": ("VAE",),
                "default_latent": ("LATENT",)
            },
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "out"
    CATEGORY = "Serving-Toolkit"

    # Todo: this is a copy of the ServingInputImage class, should be refactored
    def convert_color(self, image):
        if len(image.shape) > 2 and image.shape[2] >= 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def load_image(self, base64_str):
        nparr = np.frombuffer(base64.b64decode(base64_str), np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        result = self.convert_color(result)
        result = result.astype(np.float32) / 255.0
        image = torch.from_numpy(result)[None,]
        return image

    def out(self, vae, serving_config, default_latent = None):
        attachment_url_key = "attachment_url_0"
        if attachment_url_key not in serving_config:
            if default_latent is not None:
                return (default_latent,)
            serving_config["serve_text_function"]("This command requires an image")
            nodes.interrupt_processing(True)
            return (None,)

        attachment_url = serving_config[attachment_url_key]
        response = requests.get(attachment_url)
        image = Image.open(io.BytesIO(response.content)).convert("RGB")

        # Convert PIL image to base64 string
        image_file = io.BytesIO()
        image.save(image_file, format='PNG')
        image_file.seek(0)
        base64_img = base64.b64encode(image_file.read()).decode('utf-8')

        # Use the base64 string to get the image tensor
        t = vae.encode(self.load_image(base64_img)[:, :, :, :3])
        return ({"samples": t},)


registered_commands = []

class CommandPickerServing:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG", {"lazy": True}),
                "command_name": ("STRING", {"multiline": False, "default": ""}),
                "should_execute": ("SHOULD_EXECUTE", {"lazy": True}),
            },
        }

    FUNCTION = "out"
    CATEGORY = "Serving-Toolkit"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    def __init__(self):
        self.commandRegistry = CommandRegistry()

    def check_lazy_status(self, serving_config, command_name, should_execute=None):
        if serving_config is None:
            self.commandRegistry.add_command(command_name)
            return ["serving_config"]

        if serving_config["is_command"](command_name):
            return ["should_execute", "serving_config"]
        return None

    def out(self, serving_config, command_name, should_execute=None):
        if serving_config.get("finalize") and should_execute is not None:
            serving_config["finalize"]()
        return {}


class AlwaysExecute:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "serving_config": ("SERVING_CONFIG", {"lazy": True}),
                "should_execute": ("SHOULD_EXECUTE", {"lazy": True}),
            },
        }

    FUNCTION = "out"
    CATEGORY = "Serving-Toolkit"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    def __init__(self):
        self.command_registry = CommandRegistry()

    def check_lazy_status(self, serving_config, should_execute):
        if serving_config is None:
            self.command_registry.add_catch_all()
            return ["serving_config"]

        return ["serving_config", "should_execute"]

    def out(self, serving_config, should_execute):
        if serving_config.get("finalize"):
            serving_config["finalize"]()
        return {}

# A dictionary that contains all nodes you want to export with their names
NODE_CLASS_MAPPINGS = {
    "ServingOutput": ServingOutput,
    "ServingInputText": ServingInputText,
    "ServingInputTextImage": ServingInputTextImage,
    "ServingInputNumber": ServingInputNumber,
    "DiscordServing": DiscordServing,
    "WebSocketServing": WebSocketServing,
    "ServingInputImage": ServingInputImage,
    "ServingTextOutput": ServingTextOutput,
    "ServingMultiImageOutput": ServingMultiImageOutput,
    "ServingInputImageAsLatent": ServingInputImageAsLatent,
    "CommandPickerServing": CommandPickerServing,
    "AlwaysExecute": AlwaysExecute
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "ServingOutput": "Serving Image/Video Output",
    "DiscordServing": "Discord Serving",
    "WebSocketServing": "WebSocket Serving",
    "ServingInputText": "Serving Input Text",
    "ServingInputTextImage": "Serving Input Text & Image",
    "ServingInputNumber": "Serving Input Number",
    "ServingInputImage": "Serving Input Image",
    "ServingTextOutput": "Serving Text Output",
    "ServingMultiImageOutput": "Serving Multi-Image Output",
    "ServingInputImageAsLatent": "Serving Input Image as Latent",
    "CommandPickerServing": "Command Picker Serving",
    "AlwaysExecute": "Always Execute"
}

