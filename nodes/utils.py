def parse_command_string(command_string, command_name):
    textAndArgs = command_string[1+ len(command_name):].strip().split('--')
    result = {}
    text = textAndArgs[0].strip()
    args = textAndArgs[1:]
    print(args)
    # The first element is the "freeText" part, remove any leading or trailing whitespace.
    result["prompt"] = text.strip()

    for arg in args:
        parts = arg.split()
        if len(parts) > 1:
            # Extract the argument name and value
            arg_name = parts[0].strip()
            arg_value = ' '.join(parts[1:]).strip()
            result[arg_name] = arg_value


    return result

import io
from PIL import Image, ImageSequence
import numpy as np
def tensorToImageConversion(images, duration):
    # Create a list to store each image as a frame
    frames = []

    for img_tensor in images:
        i = 255. * img_tensor.cpu().numpy()
        img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        frames.append(img_pil)

    # Create a GIF from the list of frames
    img_byte_array = io.BytesIO()
    frames[0].save(img_byte_array, save_all=True, append_images=frames[1:], format='WEBP', duration=duration, loop=0, quality=100, lossless=True)

    img_byte_array.seek(0)
    return img_byte_array


# This class is used to store the commands that are registered by the user.
class CommandRegistry:
    _instance = None
    catch_all = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.commands = []
        return cls._instance

    def add_command(self, command):
        self.commands.append(command)

    def get_commands(self):
        return self.commands

    def clear_commands(self):
        self.commands.clear()

    def has_command(self, command):
        return command in self.commands or self.catch_all

    def add_catch_all(self):
        self.catch_all = True

