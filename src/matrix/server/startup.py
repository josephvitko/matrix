import os
import uuid
from functools import wraps
from typing import Optional

from flask import Flask, request, jsonify
from pydantic import ValidationError

from matrix.common.schema import output


# Retrieve the root from the environment variable or set to a default value
ROOT = os.getenv('FS_ROOT', '/Users/josephvitko/PycharmProjects/matrix/test/root')


def full_path(partial):
    if partial.startswith("/"):
        partial = partial[1:]
    return os.path.join(ROOT, partial)


def handle_request(input_class: type, operation_func, required_args: list[str], expects_output=False):
    """
    Handle a request by parsing the input, calling the operation function and returning a response.
    :param input_class: The input class to parse the request JSON into
    :param operation_func: The function to call with the parsed input
    :param required_args: The arguments required by the operation function
    :param expects_output: Whether the operation function returns output
    """
    try:
        input_data = input_class(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    request_id: str = uuid.uuid4().hex
    status: str
    error: Optional[str] = None
    data: Optional[output.FuseOutput] = None
    try:
        operation_args = {arg: getattr(input_data, arg) for arg in required_args}

        if "path" in operation_args:
            operation_args["path"] = full_path(operation_args["path"])

        # print(f"{request_id}: Calling {operation_func.__name__} with args: {operation_args}")
        result = operation_func(**operation_args)

        status = "success"
        if expects_output:
            data = result
    except Exception as e:
        status = "error"
        error = str(e)

    response = output.FuseResponse(status=status, error=error, data=data)

    # print(f"{request_id}: Returning response: {status}, {error}, {data}")

    return jsonify(response.model_dump())


def create_endpoint(input_class: type, operation_func, required_args: list[str], expects_output=False):
    """
    Create an endpoint function that calls the operation function with the correct arguments.
    :param input_class: The input class to parse the request JSON into
    :param operation_func: The function to call with the parsed input
    :param required_args: The arguments required by the operation function
    :param expects_output: Whether the operation function returns output
    """
    @wraps(operation_func)
    def endpoint_func():
        return handle_request(input_class, operation_func, required_args, expects_output)
    return endpoint_func


def register_endpoints(flask_app: Flask, config: dict):
    """
    Register all endpoints in the given configuration dictionary.
    :param flask_app: The Flask application to register the endpoints with
    :param config: The configuration dictionary mapping endpoints to settings
    """
    for route, settings in config.items():
        endpoint_func = create_endpoint(
            settings['input_type'],
            settings['func'],
            settings.get('args', []),
            settings.get('output_type') is not None
        )
        flask_app.add_url_rule(route, view_func=endpoint_func, methods=['POST'])