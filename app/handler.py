from app.app_runner import AppRunner
from app.utils import logger


def lambda_handler(event, context=None):
    """Lambda project handler"""

    try:
        app_runner = AppRunner(event=event)
        result = app_runner.run()
    except Exception as err:
        logger.exception(err)
        raise err
    else:
        return result
