import time
from flask import Flask, request, Response
from helper import *

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/telegram", methods=["POST"])
def telegram():
    # try:
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
        if personID in timer and time.time() - timer[personID] < coolDownTime:
            sendMessage(
                chat_id,
                "Please wait "
                + str(int(coolDownTime - time.time() + timer[personID]))
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
    elif (
        inputText.startswith(img2imgcommand)
        and len(get_required_text(inputText, img2imgcommand)) > 0
    ):
        if personID in timer and time.time() - timer[personID] < coolDownTime:
            sendMessage(
                chat_id,
                "Please wait "
                + str(int(coolDownTime - time.time() + timer[personID]))
                + " seconds before generating another image",
                messageID,
            )
        else:
            timer[personID] = time.time()
            photoFileID = msg["message"]["reply_to_message"]["photo"][-1]["file_id"]
            photoFile = requests.get(
                "https://api.telegram.org/bot"
                + botToken
                + "/getFile?file_id="
                + photoFileID
            )
            photoFile = photoFile.json()["result"]["file_path"]
            photoFile = requests.get(
                "https://api.telegram.org/file/bot" + botToken + "/" + photoFile
            )
            photoFile = Image.open(io.BytesIO(photoFile.content))
            imagePrompt = get_required_text(inputText, img2imgcommand)
            output_file = generateImageFromImage(imagePrompt, photoFile)
            if output_file:
                sendImage(chat_id, output_file, messageID)
        # else:
        #     sendMessage(
        #         chat_id, "Invalid Command. Please type /generate <prompt>", messageID
        #     )
    # except:
    #     pass
    return Response("ok", status=200)
