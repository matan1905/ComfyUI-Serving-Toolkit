import time
import threading
from .discord_client import discord_client
import threading
from collections import deque
from .utils import parse_command_string, tensorToImageConversion
import discord
import asyncio
import websocket
import json
import base64



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
        }

    RETURN_TYPES = ()
    # RETURN_NAMES = ("image_output_name",)

    FUNCTION = "out"

    OUTPUT_NODE = True

    CATEGORY = "Serving-Toolkit"

    def out(self, image,serving_config,frame_duration):
        serving_config["serve_image_function"](image,frame_duration)
        return {}


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

    RETURN_TYPES = ("FLOAT", "INT")

    FUNCTION = "out"

    CATEGORY = "Serving-Toolkit"

    def out(self, serving_config, argument,default, min_value, max_value, step):
        val = default
        if argument in serving_config and serving_config[argument].replace('.','',1).isdigit():
            val = serving_config[argument]
        valFloat = min(max(float(val), min_value), max_value) // step * step
        valInt = round(valFloat)
        return (valFloat,valInt)


class DiscordServing():
    discord_running = False
    def __init__(self):
        self.registered_command = False
        self.data_ready = threading.Event()
        self.data = deque()
        self.discord_token = None
        pass

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

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")
    # OUTPUT_NODE = False

    CATEGORY = "Serving-Toolkit"

    def serve(self, command_name, discord_token):
        if not DiscordServing.discord_running:
            self.discord_token = discord_token
            run_discord = threading.Thread(target=self.discord_runner)
            run_discord.start()
            print("Client running")
            DiscordServing.discord_running = True
        if not self.registered_command: 
            self.registered_command = True   
            @discord_client.command(name=command_name)
            async def execute(ctx):
                parsed_data = parse_command_string(ctx.message.content,command_name)
                def serve_image_function(image, frame_duration):
                    image_file = tensorToImageConversion(image, frame_duration)
                    asyncio.run_coroutine_threadsafe(ctx.reply(file=discord.File(image_file, filename='image.webp')), discord_client.loop)
                parsed_data["serve_image_function"] = serve_image_function
                parsed_data.update({f"attachment_url_{i}": attachment.url for i, attachment in enumerate(ctx.message.attachments)}) # populates all the attachments urls
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
        pass
    def on_message(self,ws,message):
        try:
            parsed = json.loads(message)
            self.data.append(parsed)
            self.data_ready.set()
        except Exception as e:
            print("Error parsing JSON", e)
        

    def ws_runner(self):
        self.ws = websocket.WebSocketApp( self.websocket_url,
                              on_message=self.on_message,)
        self.ws.run_forever(reconnect=1)

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
        def serve_image_function(image, frame_duration):
                    image_file = tensorToImageConversion(image, frame_duration)
                    base64_img = base64.b64encode(image_file.read()).decode('utf-8')
                    response= {
                        "base64_img":base64_img,
                        "_requestId":data["_requestId"] # It's assumed that it will exist.
                    }
                    self.ws.send(json.dumps(response))
        data["serve_image_function"] = serve_image_function

        return (data,)


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "ServingOutput": ServingOutput,
    "ServingInputText": ServingInputText,
    "ServingInputNumber": ServingInputNumber,
    "DiscordServing": DiscordServing,
    "WebSocketServing": WebSocketServing
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "ServingOutput": "Serving Output",
    "DiscordServing": "Discord Serving",
    "WebSocketServing": "WebSocket Serving",
    "ServingInputText": "Serving Input Text",
    "ServingInputNumber": "Serving Input Number",
}


# input - simply a push
