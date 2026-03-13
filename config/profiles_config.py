import boto3
from botocore.exceptions import ClientError

PROFILES_TABLE = "parking-permit-profiles"


def get_profile(name: str) -> dict | None:
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(PROFILES_TABLE)
    try:
        response = table.get_item(Key={"name": name})
    except ClientError as e:
        raise e
    return response.get("Item")
