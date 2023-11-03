# ComfyUI Serving Toolkit
Welcome to the ComfyUI Serving Toolkit, a powerful tool for serving image generation workflows in Discord and other platforms (soon).
This toolkit is designed to simplify the process of serving your ComfyUI workflow, making image generation bots easier than ever before.
Currently only discord is supported.

## Features
* Allows both Images or videos (when in batch mode, such as animatediff - if you return more than one image it will create a video)
* Add arguments with default values, then allow your users to use them
* Serve from your own computer, workflow is not inserted into the images so your secrets are 100% safe

## Installation
[Use ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager)

## The simplest configuration
Here a simple workflow that will get a !generate \<prompt> and resond with an image
![image](https://github.com/matan1905/ComfyUI-Serving-Toolkit/assets/24731932/e193be18-7b83-4f44-b119-21230f0b9a16)

You can copy the workflow json:
[discordserv.json](https://github.com/matan1905/ComfyUI-Serving-Toolkit/files/13248566/discordserv.json)



## Running
After setting up your workflow, In order for the serving to always be up, you need to allow auto queue, here is an image to help you do that:
![image](https://github.com/matan1905/ComfyUI-Serving-Toolkit/assets/24731932/d8f7b486-725d-4934-b72d-1a042b5f355a)




## Nodes
**DiscordServing**

This node is an essencial part of the serving, queueing the prompt it will wait for a single message, process it and optionally return the image.
Note that in order for it to work for all messages you would have to mark `Auto Queue` (details above in the running section)

Inputs:
* discord_token - [here is how you get one](https://www.writebots.com/discord-bot-token/) , make sure to enable message viewing intent
* command_name - the command used to generate, without the '!'. defaults to generate (so you would have to do !generate \<your prompt> --your_argument1 \<argument value>

Outputs:
* Serving Config - A basic reference for this serving, used by the other nodes of this toolkit to get arguments and return images.
  


**ServingInputText** 

Allows you to grab a text arguments from the request

Discord example:

When a user types: !generate 4k epic realism portrait --negative drawing
you could set the argument=negative and then recieve the value of "drawing" inside the output text.


Inputs:
* serving_config - a config made by a serving node
* argument - the argument name, the prompt itself will be inside the "prompt" argument. When using discord serving, you can access attachments url using 'attachment_url_0' (and attachment_url_1 etc). then you can use nodes like WAS Image Load to download these images
* default - the default value of this argument

Outputs:
text - the value of the argument




**ServingInputNumber**

similar to ServingInputText, this one is for numbers. it is important to set the minimum, maximum and step to the right values in order to avoid errors (for example when trying a width that does isn't divisable by 16)
Inputs that are not in ServingInputText:
* max_value - the maximum value of this argument
* min_value - the minimum value of this argument
* step - the steps of this value (setting this to 1 will ensure only whole numbers, 0.5 will allow jumps of half etc)

**ServingOutput**

Allows you to return an image/video back to the request
Inputs:
* image - the generated image. note that if this is more than one image (for example in the case of batches or animatediff frames) it will return a video
* duration - in the case of a video, what is the time in miliseconds each frame should appear? if you have an FPS number you can use 1000/FPS to calculate the duration value











