import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class AppSheetAPI:
    def __init__(self):
        self.app_id = os.getenv("APPSHEET_APP_ID")
        self.access_key = os.getenv("APPSHEET_ACCESS_KEY")
        self.base_url = f"https://api.appsheet.com/api/v2/apps/{self.app_id}/tables"

    def send_action(self, table_name, action, rows):
        """
        Envía una acción (Add, Edit, Delete, Find) a una tabla de AppSheet.
        """
        url = f"{self.base_url}/{table_name}/Action"
        headers = {
            "ApplicationAccessKey": self.access_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "Action": action,
            "Properties": {
                "Locale": "es-ES",
                "Timezone": "Central America Standard Time"
            },
            "Rows": rows
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "response": response.text if response else "No response"}
