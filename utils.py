from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter


formatter = LambdaPowertoolsFormatter(
    utc=False, log_record_order=["level", "message", "location"]
)
logger = Logger(service="parking-permit-bot", logger_formatter=formatter)
