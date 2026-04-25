
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def list_drive_files():
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    print(f"Listing files in folder: {folder_id}")
    
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_authorized_user_info(creds_dict)
    else:
        authorized_user_file = os.path.expanduser('~/.config/gspread/authorized_user.json')
        if os.path.exists(authorized_user_file):
            creds = Credentials.from_authorized_user_file(authorized_user_file)
        else:
            print("No credentials found.")
            return

    service = build('drive', 'v3', credentials=creds)
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, pageSize=20, fields="files(id, name, createdTime)").execute()
    items = results.get('files', [])

    if not items:
        print("No files found.")
    else:
        print("Files found (latest 20):")
        for item in items:
            print(f"- {item['name']} (ID: {item['id']}, Created: {item['createdTime']})")

if __name__ == "__main__":
    list_drive_files()
