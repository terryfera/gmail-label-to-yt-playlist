from __future__ import print_function
import pickle
import os.path
import json
import re
import googleapiclient.discovery
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

api_service_name = "youtube"
api_version = "v3"


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
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)
    youtube = build(api_service_name, api_version, credentials=creds)

    unread_msgs = (
        service.users()
        .messages()
        .list(userId="me", q="label:kf_patreon_videos is:unread")
        .execute()
    )

    if unread_msgs["resultSizeEstimate"] == 0:
        print("No messages found.")
    else:
        for message in unread_msgs["messages"]:

            messageId = str(message["id"])
            summ_message = (
                service.users()
                .messages()
                .get(userId="me", id=messageId, format="minimal")
                .execute()
            )

            regex = r"https:\/\/youtu.be\/([\w.,@?^=%&:~+#-]*[\w@?^=%&\/~+#-])?"

            vid_link = re.search(regex, str(summ_message["snippet"]))
            try:
                resourceId = vid_link.group(1)
            except Exception as e:
                print(e)

            print(f"Trying to add video with ResourceID: {resourceId}")

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

                print(
                    f"Video: {response['snippet']['title']} added to playlist. Video ID: {resourceId}"
                )
            except Exception as e:
                print(e)

            # Mark Message as read
            removeLabels = {"removeLabelIds": ["UNREAD"]}
            try:
                service.users().messages().modify(
                    userId="me", id=messageId, body=removeLabels
                ).execute()

                print(f"Email marked as read for Video ID: {resourceId}")

            except Exception as e:
                print(e)


if __name__ == "__main__":
    main()
