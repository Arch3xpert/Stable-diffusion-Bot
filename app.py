import os, time, io, json, warnings, requests
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from flask import Flask, request, Response
from c8 import C8Client

app = Flask(__name__)

numberOfImages = 2  # Maximum 10, Minimum 2
stepsForNormal = 50  # Maximum 150, Minimum 10
stepsForSudo = 120  # Maximum 150, Minimum 10
sudoUserSubscribeMessage = (
    "You are not authorized to use this command. Please use /generate instead."
)
APIErrorMessage = "Your request activated the API's safety filters and could not be processed.\nPlease modify the prompt and try again."


# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ["STABILITY_HOST"] = "grpc.stability.ai:443"
STABILITY_KEY = os.environ["STABILITY_KEY"]
botToken = os.environ["BOTTOKEN"]
adminUserID = os.environ["ADMINUSERID"]
MACROMETA_KEY = os.environ["MACROMETA"]
collection_name = "users"
timer = {}


def getAllSudoUsers():
    client = C8Client(
        protocol="https", host="play.paas.macrometa.io", port=443, apikey=MACROMETA_KEY
    )
    if not client.has_collection(collection_name):
        client.create_collection_kv(name=collection_name)
    try:
        return client.get_value_for_key(collection_name, "userid")
    except:
        return ""


def sudoUserCheck(userID):
    allUsers = getAllSudoUsers()
    if allUsers == "":
        return False
    allUsers = allUsers["value"].split()
    if str(userID) in allUsers:
        return True
    return False


def sudoUserAdd(newUserID):
    client = C8Client(
        protocol="https", host="play.paas.macrometa.io", port=443, apikey=MACROMETA_KEY
    )
    response = getAllSudoUsers()
    try:
        currentUsers = str(response["value"])
    except:
        currentUsers = ""
    allUsers = currentUsers + " " + newUserID
    newValue = " ".join(list(set(allUsers.split())))
    client.insert_key_value_pair(collection_name, {"_key": "userid", "value": newValue})


def startFunction(chatid, messageID):
    url = f"https://api.telegram.org/bot{botToken}/sendPhoto"
    payload = {
        "chat_id": chatid,
        "photo": "https://files29.s3.us-west-004.backblazeb2.com/photo1675232544.jpeg",
        "caption": "Bot made by @Archxpert\n\nUse command /generate { prompt here } to generate a image",
        "reply_to_message_id": messageID,
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


def sendMediaGroup(chatid, allImages, messageID):
    url = f"https://api.telegram.org/bot{botToken}/sendMediaGroup"
    payload = {
        "chat_id": chatid,
        "media": wholeJsonMaker(allImages),
        "reply_to_message_id": messageID,
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


def get_required_text(text, prefix):
    parts = text.split(" ")
    if parts[0].startswith(prefix):
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


def sendMessage(chat_id, text, messageID):
    url = f"https://api.telegram.org/bot{botToken}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "reply_to_message_id": messageID}
    r = requests.post(url, json=payload)
    return r


# Sign up for an account at the following link to get an API Key.
# https://beta.dreamstudio.ai/membership

# Click on the following link once you have created an account to be taken to your API Key.
# https://beta.dreamstudio.ai/membership?tab=apiKeys

# Paste your API Key below.


def stabilityAI(imagePrompt, steps):
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
        steps=steps,
        cfg_scale=8.0,  # Influences how strongly your generation is guided to match your prompt.
        # Setting this value higher increases the strength in which it tries to match your prompt.
        # Defaults to 7.0 if not specified.
        width=512,  # Generation width, defaults to 512 if not included.
        height=512,  # Generation height, defaults to 512 if not included.
        samples=numberOfImages,  # Number of images to generate, defaults to 1 if not included.
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
        messageID = msg["message"]["message_id"]
        personID = chat_id
        if msg["message"].get("from") is not None:
            personID = msg["message"]["from"]["id"]
        if inputText.startswith("/start"):
            startFunction(chat_id, messageID)
        elif (
            inputText.startswith("/generate")
            and len(get_required_text(inputText, "/generate")) > 0
        ):
            if personID in timer and time.time() - timer[personID] < 60:
                sendMessage(
                    chat_id,
                    "Please wait "
                    + str(int(60 - time.time() + timer[personID]))
                    + " seconds before generating another image",
                    messageID,
                )
            else:
                timer[personID] = time.time()
                imagePrompt = get_required_text(inputText, "/generate")
                fileNames = stabilityAI(imagePrompt, stepsForNormal)
                if len(fileNames) < 1:
                    sendMessage(
                        chat_id,
                        APIErrorMessage,
                        messageID,
                    )
                else:
                    allImages = [
                        (fileNames[i], imagePrompt) for i in range(len(fileNames))
                    ]
                    sendMediaGroup(chat_id, allImages, messageID)
        elif (
            inputText.startswith("/imagine")
            and len(get_required_text(inputText, "/imagine")) > 0
        ):
            imagePrompt = get_required_text(inputText, "/imagine")
            if sudoUserCheck(personID) == False:
                sendMessage(
                    chat_id,
                    sudoUserSubscribeMessage,
                    messageID,
                )
            else:
                fileNames = stabilityAI(imagePrompt, stepsForSudo)
                if len(fileNames) < 1:
                    sendMessage(
                        chat_id,
                        APIErrorMessage,
                        messageID,
                    )
                else:
                    allImages = [
                        (fileNames[i], imagePrompt) for i in range(len(fileNames))
                    ]
                    sendMediaGroup(chat_id, allImages, messageID)
        elif (
            inputText.startswith("/addusersecret")
            and len(get_required_text(inputText, "/addusersecret")) > 0
        ):
            if str(personID) != str(adminUserID):
                sendMessage(
                    chat_id,
                    "You are not authorized to use this command",
                    messageID,
                )
            else:
                sudoUserAdd(get_required_text(inputText, "/addusersecret"))
                sendMessage(
                    chat_id,
                    "User added successfully",
                    messageID,
                )
        else:
            sendMessage(
                chat_id, "Invalid Command. Please type /generate <prompt>", messageID
            )
        return Response("ok", status=200)
    except:
        return Response("ok", status=200)
