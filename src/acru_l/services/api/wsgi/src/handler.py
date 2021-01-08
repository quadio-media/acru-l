import os

from apig_wsgi import make_lambda_handler
from acrul_toolkit.module_loading import import_string


WSGI_APPLICATION = os.environ.get("WSGI_APPLICATION")
application = import_string(WSGI_APPLICATION)
handle_request = make_lambda_handler(application, binary_support=True)


def main(event, context):
    if "httpMethod" not in event:
        return {"status": "success"}
    return handle_request(event, context)
