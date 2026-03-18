import json
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from app.utils import logger

SESSIONS_TABLE = "parking-permit-sessions"
PROFILES_TABLE = "parking-permit-profiles"
ADMIN_NUMBER = "+19402311617"
EXPECTED_FIELDS = ["firstName", "lastName", "phoneNumber", "licensePlate", "state", "year", "make", "model", "color"]
SESSION_TTL_SECONDS = 300


class AddProfileHandler:
    def __init__(self, sender: str, message_text: str, send_message_fn):
        self.sender = sender
        self.message_text = message_text.strip()
        self.send_message = send_message_fn
        self.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        self.sessions_table = self.dynamodb.Table(SESSIONS_TABLE)
        self.profiles_table = self.dynamodb.Table(PROFILES_TABLE)

    def handle(self) -> bool:
        """Returns True if message was consumed by this handler."""
        if self.sender != ADMIN_NUMBER:
            return False

        session = self._get_session()

        if session and session.get("step") == "awaiting_confirm":
            self._handle_confirmation(session)
            return True

        if self.message_text.lower().startswith("add "):
            self._handle_add_command()
            return True

        return False

    def _handle_add_command(self):
        raw = self.message_text[4:].strip()
        parts = [p.strip() for p in raw.split(",")]

        if len(parts) != len(EXPECTED_FIELDS):
            self.send_message(
                f"Expected {len(EXPECTED_FIELDS)} comma-separated values:\n"
                f"firstName, lastName, phoneNumber, licensePlate, state, year, make, model, color\n\n"
                f"Got {len(parts)}. Please try again.",
                to=self.sender,
            )
            return

        data = dict(zip(EXPECTED_FIELDS, parts))
        data["licensePlate"] = data["licensePlate"].upper()
        data["name"] = data["firstName"].lower()

        self._save_session(data)

        profile_json = json.dumps({k: data[k] for k in ["name"] + EXPECTED_FIELDS}, indent=2)
        self.send_message(
            f"Here's the profile to be added:\n\n{profile_json}\n\nReply YES to save or NO to cancel.",
            to=self.sender,
        )

    def _handle_confirmation(self, session):
        response = self.message_text.upper()
        data = session.get("data", {})

        if response == "YES":
            self._write_profile(data)
            self._delete_session()
            self.send_message(
                f"Profile for {data.get('firstName')} {data.get('lastName')} added successfully!",
                to=self.sender,
            )
        else:
            self._delete_session()
            self.send_message("Profile creation cancelled.", to=self.sender)

    def _write_profile(self, data):
        self.profiles_table.put_item(Item=data)
        logger.info(f"new profile written: {data.get('name')}")

    def _get_session(self):
        try:
            response = self.sessions_table.get_item(Key={"sender": self.sender})
            return response.get("Item")
        except ClientError as e:
            logger.error(f"error getting session: {e}")
            return None

    def _save_session(self, data):
        ttl = int(datetime.now(timezone.utc).timestamp()) + SESSION_TTL_SECONDS
        self.sessions_table.put_item(Item={
            "sender": self.sender,
            "step": "awaiting_confirm",
            "data": data,
            "ttl": ttl,
        })

    def _delete_session(self):
        self.sessions_table.delete_item(Key={"sender": self.sender})
