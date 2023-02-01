import os
import io
import json
import warnings
import requests
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from flask import Flask, request, Response

app = Flask(__name__)

# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ["STABILITY_HOST"] = "grpc.stability.ai:443"
STABILITY_KEY = os.environ["STABILITY_KEY"]
botToken = os.environ["botToken"]


def startFunction(chatid):
    url = f"https://api.telegram.org/bot{botToken}/sendPhoto"
    payload = {
        "chat_id": chatid,
        "photo": "AgACAgQAAxkBAAEcpKRj2ghW_nPIyn3493KYEtVwUch9kgACErAxG5Tv1VJ1WtlPA4QXbwEAAwIAA3gAAy4E",
        "caption": "Bot made by @Archxpert\n\nUse command /generate { prompt here } to generate a image",
    }
    r = requests.post(url, data=payload)
    return r


def wholeJsonMaker(allImages):
    finalJSON = []
    for i in range(len(allImages)):
        finalJSON.append(
            {
                "type": "photo",
                "media": "attach://" + allImages[i][0],
                "caption": allImages[i][1],
            }
        )
    return json.dumps(finalJSON)


def sendMediaGroup(chatid, allImages):
    url = f"https://api.telegram.org/bot{botToken}/sendMediaGroup"
    payload = {
        "chat_id": chatid,
        "media": wholeJsonMaker(allImages),
    }
    files = [
        (
            allImages[i][0],
            (
                allImages[i][0],
                open("/tmp/" + allImages[i][0], "rb"),
                "image/png",
            ),
        )
        for i in range(len(allImages))
    ]
    r = requests.post(url, data=payload, files=files)
    # print(r.text)
    return r


def get_required_text(text):
    parts = text.split(" ")
    if parts[0].startswith("/generate"):
        required_text = " ".join(parts[1:])
        return required_text.split("@")[0]
    return None


def sendPhoto(chatid, allImages):
    url = f"https://api.telegram.org/bot{botToken}/sendPhoto?chat_id={chatid}"
    files = [
        (
            "photo",
            (
                "allImages[0][0]",
                open(
                    "/tmp/" + allImages[0][0],
                    "rb",
                ),
                "image/png",
            ),
        )
    ]
    r = requests.post(url, files=files)
    print(r.text)
    return r


def sendMessage(chat_id, text):
    url = f"https://api.telegram.org/bot{botToken}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    r = requests.post(url, json=payload)
    return r


# Sign up for an account at the following link to get an API Key.
# https://beta.dreamstudio.ai/membership

# Click on the following link once you have created an account to be taken to your API Key.
# https://beta.dreamstudio.ai/membership?tab=apiKeys

# Paste your API Key below.


def stabilityAI(imagePrompt):
    # Set up our connection to the API.
    stability_api = client.StabilityInference(
        key=STABILITY_KEY,  # API Key reference.
        verbose=True,  # Print debug messages.
        engine="stable-diffusion-512-v2-1",  # Set the engine to use for generation.
        # Available engines: stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
        # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-inpainting-v1-0 stable-inpainting-512-v2-0
    )

    # Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=imagePrompt,
        steps=50,
        cfg_scale=8.0,  # Influences how strongly your generation is guided to match your prompt.
        # Setting this value higher increases the strength in which it tries to match your prompt.
        # Defaults to 7.0 if not specified.
        width=512,  # Generation width, defaults to 512 if not included.
        height=512,  # Generation height, defaults to 512 if not included.
        samples=2,  # Number of images to generate, defaults to 1 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M  # Choose which sampler we want to denoise our generation with.
        # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
        # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m)
    )

    # Set up our warning to print to the console if the adult content classifier is tripped.
    # If adult content classifier is not tripped, save generated images.
    fileNames = []
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again."
                )
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                img.save(
                    "/tmp/" + str(artifact.seed) + ".png"
                )  # Save our generated images with their seed number as the filename.
                fileNames.append(str(artifact.seed) + ".png")
    return fileNames


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/telegram", methods=["POST"])
def telegram():
    try:
        msg = request.get_json()
        chat_id = msg["message"]["chat"]["id"]
        inputText = msg["message"]["text"]
        if inputText == "/start":
            startFunction(chat_id)
        elif (
            inputText.startswith("/generate") and len(get_required_text(inputText)) > 0
        ):
            imagePrompt = get_required_text(inputText)
            fileNames = stabilityAI(imagePrompt)
            if len(fileNames) < 1:
                sendMessage(
                    chat_id,
                    "Your request activated the API's safety filters and could not be processed.\nPlease modify the prompt and try again.",
                )
            else:
                allImages = [(fileNames[i], imagePrompt) for i in range(len(fileNames))]
                sendMediaGroup(chat_id, allImages)
        else:
            sendMessage(chat_id, "Invalid Command. Please type /generate <prompt>")
        return Response("ok", status=200)
    except:
        return Response("ok", status=200)
