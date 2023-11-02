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
from PIL import Image
def tensorToImageConversion(img_tensor ):
    img_tensor = (img_tensor * 255).byte()
    img_array = img_tensor.squeeze(0).numpy()
    img_pil = Image.fromarray(img_array)
    img_byte_array = io.BytesIO()
    img_pil.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)
    return img_byte_array


