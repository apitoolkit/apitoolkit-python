import base64
import time
from datetime import datetime
import traceback
import requests
from jsonpath_ng import parse  # type: ignore
import json
import pytz  # type: ignore
import httpx  # type: ignore


def observe_request(parent_request, url_wildcard=None, redact_headers=[], redact_request_body=[], redact_response_body=[]):
    start_time = 0
    req = None

    def on_request(request):
        nonlocal start_time, req
        start_time = time.perf_counter_ns()
        req = request
        return request

    def on_response(response):
        response.read()
        message_id = parent_request.apitoolkit_message_id if hasattr(
            parent_request, "apitoolkit_message_id") else parent_request.state.apitoolkit_message_id if hasattr(parent_request.state, "apitoolkit_message_id") else None
        if message_id is None:
            print(
                "No message_id found attached to request, make sure middleware is configured correctly")

        apitoolkitClient = parent_request.apitoolkit_client if hasattr(
            parent_request, "apitoolkit_client") else parent_request.state.apitoolkit_client if hasattr(
            parent_request.state, "apitoolkit_client") else None
        if apitoolkitClient is None:
            print(
                "No client found attached to request, make sure middleware is configured correctly")
        clientInfo = apitoolkitClient.getInfo()
        payload = build_payload(start_time, req, response, req.content.decode(), response.text,
                                redact_request_body, redact_response_body, redact_headers, clientInfo["project_id"], clientInfo["service_version"], [], clientInfo["tags"], message_id, url_wildcard)
        apitoolkitClient.publish_message(payload)

    client = httpx.Client(event_hooks={'request': [
        on_request], 'response': [on_response]})

    return client


def build_payload(start_time, req, res, req_body, resp_body, redact_request_body, redact_response_body, redact_header_lists, project_id, service_version, errors, tags, parent_id, url_wildcard):
    def redact_fields(data, redact_list):
        for field in redact_list:
            data = data.replace(field, "[REDACTED]")
        return data

    req_headers = dict((k, v if isinstance(v, list) else [
                       v]) for k, v in req.headers.items())
    res_headers = dict((k, v if isinstance(v, list) else [v]) for k, v in (
        res.headers if res else {}).items())

    path_and_query = get_path_and_query_params_from_url(req.url) if req.url else {
        "path": "", "queryParams": {}, "rawUrl": ""}
    url_path = url_wildcard or req.url.path
    timezone = pytz.timezone("UTC")
    timestamp = datetime.now(timezone).isoformat()

    payload = {
        "duration": time.perf_counter_ns() - start_time,
        "host": req.url.host if req.url else "",
        "method": req.method.upper() if req.method else "",
        "path_params": {},
        "project_id": project_id,
        "proto_minor": 1,
        "proto_major": 1,
        "query_params": path_and_query["queryParams"],
        "raw_url": req.url.path,
        "referer": req_headers.get("referer", ""),
        "request_body": base64.b64encode(redact_fields(req_body, redact_request_body).encode()).decode(),
        "request_headers": redact_headers(req_headers, redact_header_lists),
        "response_body": base64.b64encode(redact_fields(resp_body, redact_response_body).encode()).decode(),
        "response_headers": redact_headers(res_headers, redact_header_lists),
        "sdk_type": "PythonOutgoing",
        "status_code": res.status_code if res else 404,
        "timestamp": timestamp,
        "url_path": url_path,
        "service_version": service_version,
        "errors": errors,
        "tags": tags,
        "parent_id": parent_id,
    }
    return payload


def redact_headers_func(headers, redact_header_list):
    redacted_headers = {}
    for header_name, value in headers.items():
        if header_name.lower() in redact_header_list or header_name in redact_header_list:
            redacted_headers[header_name] = "[CLIENT_REDACTED]"
        else:
            redacted_headers[header_name] = value
    return redacted_headers


def redact_fields(body, paths):
    try:
        data = json.loads(body)
        for path in paths:
            expr = parse(path)
            expr.update(data, "[CLIENT_REDACTED]")
        return json.dumps(data).encode("utf-8")
    except Exception as e:
        if isinstance(body, str):
            return body.encode('utf-8')
        return body


def redact_headers(headers, redact_header_lists):
    for header_list in redact_header_lists:
        for header in header_list:
            if header in headers:
                headers[header] = "[REDACTED]"
    return headers


def get_path_and_query_params_from_url(url):
    try:
        parsed_url = requests.utils.urlparse(url)
        path = parsed_url.path
        query_params = dict(requests.utils.parse_qsl(parsed_url.query))
        raw_url = url
        return {"path": path, "queryParams": query_params, "rawUrl": raw_url}
    except Exception as e:
        return {"path": "", "queryParams": {}, "rawUrl": ""}


class ATError:
    def __init__(self, error):
        timezone = pytz.timezone("UTC")
        self.error_info = {
            'when': datetime.now(timezone).isoformat(),
            'error_type': type(error).__name__,
            'message': str(error),
            'stack_trace': traceback.format_exc()
        }
        root_error = self.get_root_error(error)
        if root_error:
            self.error_info['root_error_type'] = type(root_error).__name__
            self.error_info['root_error_message'] = str(root_error)

    def to_dict(self):
        return self.error_info

    def get_root_error(self, error):
        while error.__cause__ is not None:
            error = error.__cause__
        return error


def report_error(request, error):
    # fast api throws error for trying to access request.apitoolkit_errors
    try:
        errors = request.apitoolkit_errors or []
        at_error = ATError(error)
        errors.append(at_error.to_dict())
        request.apitoolkit_errors = errors
    except Exception as e:
        errors = request.state.apitoolkit_errors or []
        at_error = ATError(error)
        errors.append(at_error.to_dict())
        request.state.apitoolkit_errors = errors
