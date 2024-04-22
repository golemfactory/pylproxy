from typing import TypedDict, Mapping, Optional


class RequestCallbackObj(TypedDict):
    method: str
    url: str
    headers: Mapping[str, str]
    content: Optional[bytes]
    path: str
    timestamp_start: float


class ResponseCallbackObj(TypedDict):
    status_code: int
    content: Optional[bytes]
    timestamp_end: float


def check_types_request(request: RequestCallbackObj):
    # precise dynamic type checking
    if not isinstance(request["method"], str):
        raise Exception("Invalid type method")

    if not isinstance(request["url"], str):
        raise Exception("Invalid type url")

    if not isinstance(request["headers"], Mapping):
        raise Exception("Invalid type headers")

    for key, value in request["headers"].items():
        if not isinstance(key, str):
            raise Exception("Invalid type key in headers")
        if not isinstance(value, str):
            raise Exception("Invalid type value in headers")

    if request["content"] is not None and not isinstance(request["content"], bytes):
        raise Exception("Invalid type content")

    if not isinstance(request["path"], str):
        raise Exception("Invalid type path")

    if not isinstance(request["timestamp_start"], float):
        raise Exception("Invalid type timestamp_start")


def check_types_response(response: ResponseCallbackObj) -> None:
    # precise dynamic type checking
    if not isinstance(response["status_code"], int):
        raise Exception("Invalid type status_code")

    if response["content"] is not None and not isinstance(response["content"], bytes):
        raise Exception("Invalid type content")
