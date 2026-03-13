from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import boto3
import json
import time
import os
from botocore.exceptions import ClientError
from twilio.rest import Client

from config.profiles_config import get_profile
from app.parking_registration import RegistrationProcessor
from app.utils import logger


class AppRunner:
    def __init__(self, event: dict):
        self.start_time = time.perf_counter()

        self.event = event
        if not self.event.get("source"):
            # event variables
            self.message_text = self.event.get("messageText")
            self.sender = self.event.get("sender")
            self.body_raw = self.event.get("body") or ""
            if self.event.get("isBase64Encoded"):
                import base64

                self.body_raw = base64.b64decode(self.body_raw).decode()

            # aws
            self.s3_bucket_name = "parking-registration-screenshots"
            self.dynamodb_table_name = "parking-registration-permits"
            self.dynamodb_resource = boto3.resource("dynamodb", region_name="us-east-1")
            self.dynamodb_client = boto3.client("dynamodb")

            # twilio
            secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
            twilio_secret = json.loads(
                secrets_client.get_secret_value(SecretId="parking-permit-bot/twilio")["SecretString"]
            )
            self.twilio_client = Client(
                twilio_secret["TWILIO_ACCOUNT_SID"], twilio_secret["TWILIO_AUTH_TOKEN"]
            )
            self.tz = ZoneInfo("America/Chicago")

    def run(self):
        logger.info(f"event received: {self.event}")
        if self.event.get("source"):
            logger.info("lambda warmed")
            return

        # find car registration profile
        text_split = self.message_text.lower().split(" ")
        is_test_mode = False
        if len(text_split) > 1:
            if text_split[1] == "test":
                is_test_mode = True

        registration_profile = get_profile(text_split[0])

        if not registration_profile:
            logger.info("car profile not found")

            response_body = f"Sorry, I wasn't able to find a registration profile that matched: '{self.message_text}' 🥺"
            self.send_message(response_text=response_body, to=self.sender)
            return

        # check dynamodb table to see if a record exists and if the registration time is in the last 72 hours
        record = self.check_name_in_dynamodb(
            first_name=registration_profile.get("firstName")
        )
        if record:
            current_datetime = datetime.now(self.tz)
            seventy_two_hours_ago = current_datetime - timedelta(hours=72)
            registration_datetime = datetime.strptime(
                record.get("dateTime"), "%Y-%m-%d %H:%M:%S"
            )
            registration_datetime = registration_datetime.replace(tzinfo=self.tz)
            if registration_datetime > seventy_two_hours_ago:
                time_difference_minutes = int(
                    (current_datetime - registration_datetime).total_seconds() // 60
                )
                logger.info(f"registered {time_difference_minutes} minutes ago")
                if time_difference_minutes > 120:
                    time_difference_string = (
                        f"{time_difference_minutes // 60} hours ago"
                    )
                else:
                    time_difference_string = f"{time_difference_minutes} minutes ago"

                response_body = (
                    f"It appears that {registration_profile.get('firstName')}'s car is already currently registered. 👍\n\n"
                    f"It was registered at:\n"
                    f"{record.get('dateTime')}\n\n"
                    f"{time_difference_string} 🕓"
                )
                self.send_message(
                    response_text=response_body,
                    to=self.sender,
                    media_url=record.get("imageUrl"),
                )
                return
            else:
                self.delete_name_in_dynamodb(
                    first_name=registration_profile.get("firstName")
                )

        # complete registration
        try:
            registration_processor = RegistrationProcessor(
                profile=registration_profile, is_test_mode=is_test_mode
            )
            screenshot_name = registration_processor.fill_out_registration()
        except Exception as err:
            response_body = f"I'm sorry, an error occurred while filling out the registration form. 😔"
            self.send_message(response_text=response_body, to=self.sender)
            raise err

        if not screenshot_name:
            response_body = (
                f"It appears that {registration_profile.get('firstName')}'s car is already currently registered.\n\n"
                f"I don't have the screenshot for it but check your email. 🤔"
            )
            self.send_message(response_text=response_body, to=self.sender)
            return

        self.upload_file_to_s3(file_name=screenshot_name)

        object_url = f"https://{self.s3_bucket_name}.s3.amazonaws.com/{screenshot_name}"

        self.put_name_in_dynamodb(
            first_name=registration_profile.get("firstName"),
            date_and_time=datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
            image_url=object_url,
        )

        response_body = (
            f"{registration_profile.get('firstName')}'s car has been registered! 😤"
        )
        self.send_message(
            response_text=response_body, to=self.sender, media_url=object_url
        )
        return

    def upload_file_to_s3(self, file_name):
        s3_client = boto3.client("s3")
        logger.info(f"uploading file '/tmp/{file_name}' to s3://{self.s3_bucket_name}/")
        try:
            s3_client.upload_file(
                Filename=f"/tmp/{file_name}",
                Bucket=self.s3_bucket_name,
                Key=file_name,
                ExtraArgs={
                    "ContentType": "image/png",
                },
            )
            logger.info(f"file uploaded successfully")
        except ClientError as e:
            logger.error(f"error uploading file: {e}")
            raise e

    def check_name_in_dynamodb(self, first_name):
        try:
            table = self.dynamodb_resource.Table(self.dynamodb_table_name)
            key = {"firstName": first_name}
            logger.info(f"checking for this item in dynamodb table: {key}")
            dynamodb_response = table.get_item(Key=key)

        except ClientError as e:
            logger.error(f"error with get_item: {e}")
            raise e

        item = dynamodb_response.get("Item")

        if item:
            logger.info(f"record found: {item}")
            return item

        logger.info("record not found")
        return None

    def delete_name_in_dynamodb(self, first_name):
        try:
            table = self.dynamodb_resource.Table(self.dynamodb_table_name)
            key = {"firstName": first_name}
            logger.info(
                f"deleting this item in dynamodb table because its over 72 hours old: {key}"
            )
            dynamodb_response = table.delete_item(Key=key)
            logger.info(f"item deleted: {dynamodb_response}")
        except ClientError as e:
            logger.error(f"error with get_item: {e}")
            raise e

    def put_name_in_dynamodb(self, first_name, date_and_time, image_url):
        item = {
            "firstName": {"S": first_name},
            "dateTime": {"S": date_and_time},
            "imageUrl": {"S": image_url},
        }

        try:
            logger.info(f"putting this item in dynamodb table: {item}")
            dynamodb_response = self.dynamodb_client.put_item(
                TableName=self.dynamodb_table_name,  # Replace with your table name
                Item=item,
            )
            logger.info(f"item added successfully: {dynamodb_response}")
        except ClientError as e:
            logger.error(f"error with put_item: {e}")
            raise e

    def send_message(self, response_text, to, media_url=None):
        message_body = f"{response_text}\n\n\n-M.O.R.G. 🤖"
        if media_url:
            message = self.twilio_client.messages.create(
                body=message_body,
                from_="+19704108487",
                media_url=[media_url],
                to=to,
            )
            logger.info(f"sent message body: {message.body}")
            self.twilio_client.messages.create(
                body=f"Sent to {self.sender}:\n\n{message_body}",
                from_="+19704108487",
                media_url=[media_url],
                to="+19402311617",
            )
        else:
            message = self.twilio_client.messages.create(
                body=f"{message_body}\n\n-M.O.R.G. 🤖",
                from_="+19704108487",
                to=to,
            )
            logger.info(f"sent message body: {message.body}")
            self.twilio_client.messages.create(
                body=f"Sent to {self.sender}:\n\n{message_body}",
                from_="+19704108487",
                to="+19402311617",
            )
