import os
# from dotenv import load_dotenv
# load_dotenv()

numberOfImages = 2  # Maximum 10, Minimum 2
stepsForNormal = 50  # Maximum 150, Minimum 10
stepsForSudo = 150  # Maximum 150, Minimum 10
sudoUserSubscribeMessage = (
    "You have no access to use this Command\n Get It From @Archxpert."
)
APIErrorMessage = "Your request activated the API's safety filters and could not be processed.\nPlease modify the prompt and try again."
coolDownTime = 0

# Our Host URL should not be prepended with "https" nor should it have a trailing slash.
os.environ["STABILITY_HOST"] = "grpc.stability.ai:443"
STABILITY_KEY = os.environ["STABILITY_KEY"]
botToken = os.environ["BOTTOKEN"]
adminUserID = os.environ["ADMINUSERID"]
MACROMETA_KEY = os.environ["MACROMETA"]
collection_name = "users"
timer = {}
img2imgcommand = "/image"
