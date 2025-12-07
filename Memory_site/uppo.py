import tkinter as tk
from tkinter import filedialog
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import os

# Google Drive API scope (file-level access)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# OAuth credentials file downloaded from Google Cloud Console
CLIENT_SECRET_FILE = "credentials.json"

# Token file to save login session
TOKEN_FILE = "token.json"

# Optional: upload into a specific folder
FOLDER_ID = "14GgB06tloAO66C7FrbZXkhR85rErz2Ka"


def choose_file():
    """Open file picker"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select a file to upload")
    return file_path


def get_credentials():
    """Authenticate user only once, then reuse token.json"""
    creds = None

    # If token.json exists → load it
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid token → do fresh login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh automatically
            creds.refresh(Request())
        else:
            # Login first time
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def upload_to_drive(file_path):
    """Upload selected file to Google Drive"""
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": os.path.basename(file_path)}
    if FOLDER_ID:
        file_metadata["parents"] = [FOLDER_ID]

    media = MediaFileUpload(file_path, resumable=True)

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    print("Upload successful!")
    print("File ID:", uploaded_file.get("id"))


if __name__ == "__main__":
    file_path = choose_file()
    if file_path:
        upload_to_drive(file_path)
    else:
        print("No file selected.")
