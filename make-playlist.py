from __future__ import print_function
import pickle
import os.path
import json
import re
import logging
import base64
import googleapiclient.discovery
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def parse_msg(msg):
    if msg['payload']['parts'][0]['body']['data']:
        msg_decode = base64.urlsafe_b64decode(
            msg['payload']['parts'][0]['body']['data']).decode("utf-8")
    return msg_decode


def link_search(msgBody):
    vid_link = re.search(regex, str(msgBody))
    logger.debug(f"Regex search result: {str(vid_link)}")
    return vid_link.group(6)


# Regex string for youtube link search
regex = r"""((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?([<"])"""


# Create and configure logger
logLocation = "./"
logfile = "yt-playlist.log"

logging.basicConfig(
    filename=logLocation + logfile,
    format="%(asctime)s - %(levelno)s-%(levelname)s - %(message)s",
    filemode="a",
    datefmt="%Y-%m-%d %I:%M:%S %p",
)

# Creating a logging object
logger = logging.getLogger(__name__)

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.ERROR)

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    unread_msgs = (
        service.users()
        .messages()
        .list(userId="me", q="label:kf_patreon_videos is:unread")
        .execute()
    )

    if unread_msgs["resultSizeEstimate"] == 0:
        logger.info("No new messages found.")
    else:
        for message in unread_msgs["messages"]:

            messageId = str(message["id"])
            full_message = (
                service.users()
                .messages()
                .get(userId="me", id=messageId, format="full")
                .execute()
            )

            # logger.debug(f"Returned details from gmail: {full_message}")

            msgBody = parse_msg(full_message)

            logger.debug(f"Decoded message body: {msgBody}")

            resourceId = ""

            try:
                resourceId = link_search(msgBody)
                logger.info(f"Found ResourceID: {resourceId}")
            except Exception as e:
                logger.error(f"Error while searching for link: {e}")

            if resourceId:
                try:
                    request = youtube.playlistItems().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "playlistId": "PL4OWSymq15n32SGsyS3Y9VG3_oEYn_cIe",
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": resourceId,
                                },
                            }
                        },
                    )
                    response = request.execute()
                    # Mark Message as read
                    removeLabels = {"removeLabelIds": ["UNREAD"]}
                except Exception as e:
                    logger.error(f"Error while inserting playlist item: {e}")

                try:
                    service.users().messages().modify(
                        userId="me", id=messageId, body=removeLabels
                    ).execute()

                    logger.info(
                        f"Email marked as read for Video ID: {resourceId}")

                except Exception as e:
                    logger.error(f"Error while marking email as read: {e}")

                logger.info(
                    f"Video: {response['snippet']['title']} added to playlist. Video ID: {resourceId}"
                )


if __name__ == "__main__":
    main()
