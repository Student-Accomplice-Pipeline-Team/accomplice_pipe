import json
import os

from datetime import datetime
from pipe.shared.helper.utilities.ui_utils import InfoDialog, TextEntryDialog


def check_lock():
    unlocked = False

    with open("/groups/accomplice/pipeline/production/assets/.publish_lock.json", "r") as lock_file:
        data = json.load(lock_file)

        current_weekday = datetime.now().strftime("%A")
        current_time = datetime.now().strftime("%H:%M")

        expected_password = data["password"]
        access_rules = data["permissions"][current_weekday]

        for rule in access_rules:
            start_time = rule["start_time"]
            end_time = rule["end_time"]

            if start_time <= current_time <= end_time:
                unlocked = True

    if not unlocked:
        entered_password = _prompt_password(expected_password)
        if not entered_password:
            return False
        
        unlocked = entered_password == expected_password

    if not unlocked:
        dialog = InfoDialog(
            "Permission Denied",
            "You were not granted permission to publish."
        )
        dialog.exec_()

        return False
    
    return True


def _prompt_password(expected_password: str):
    dialog = TextEntryDialog(
        dialog_title="Enter Password",
        dialog_message="Publishing is locked at this time. Please enter the publishing password to continue.",
        is_password=True
    )

    if dialog.exec_():
        entered_password = dialog.get_text_entry()
        return entered_password
