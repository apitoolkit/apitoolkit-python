import base64
import datetime
import time
import traceback
import requests
from jsonpath_ng import parse
import json


def observe_requests(parentRequest, url_wildcard=None, redact_headers=None, redact_request_body=None, redact_response_body=None):
    session = requests.Session()
    start_time = 0
    req = None

    def on_request_prepared(request, *args, **kwargs):
        nonlocal start_time, req
        start_time = time.perf_counter_ns()
        req = request
        print("Request URL:", request.url)
        print("Request Headers:", request.headers)
        print("Request Data:", request.data)
        return request

    def on_response_received(response, *args, **kwargs):
        print("Response URL:", response.url)
        print("Response Headers:", response.headers)

        if response.status_code >= 400:
            print("HTTP Error:", response.status_code)
            print("Response Content:", response.text)

        if response.status_code == 200:
            print("Response Content:", response.text)
        errors = parentRequest.get("apitoolkit_errors", None)
        if errors is None:
            print(
                "No errors found attached to request, make sure middleware is configure correctly")

        message_id = parentRequest.get("apitoolkit_message_id", None)
        if message_id is None:
            print(
                "No message_id found attached to request, make sure middleware is configure correctly")
        client = parentRequest.get("apitoolkit_client", None)
        if client is None:
            print(
                "No client found attached to request, make sure middleware is configure correctly")

        payload = build_payload(start_time, req, req.data, response.text, redact_request_body, redact_response_body,
                                redact_headers, client.project_id, client.service_version, [], client.tags, message_id, url_wildcard)
        client.publishMessage(payload)
        return response

    session.hooks['pre_request'] = [on_request_prepared]
    session.hooks['response'] = [on_response_received]

    return session


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
    url_path = url_wildcard or path_and_query["path"]

    payload = {
        "duration": int((time.time() * 1000000000) - start_time),
        "host": req.url if req.url else "",
        "method": req.method.upper() if req.method else "",
        "path_params": {},
        "project_id": project_id,
        "proto_minor": 1,
        "proto_major": 1,
        "query_params": path_and_query["queryParams"],
        "raw_url": path_and_query["rawUrl"],
        "referer": req_headers.get("referer", ""),
        "request_body": base64.b64encode(redact_fields(req_body, redact_request_body).encode()).decode(),
        "request_headers": redact_headers(req_headers, redact_header_lists),
        "response_body": base64.b64encode(redact_fields(resp_body, redact_response_body).encode()).decode(),
        "response_headers": redact_headers(res_headers, redact_header_lists),
        "sdk_type": "PythonOutgoing",
        "status_code": res.status_code if res else 404,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
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
        self.error_info = {
            'when': datetime.now().isoformat(),
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
    errors = request.get("apitoolkit_errors", [])
    at_error = ATError(error)
    errors.append(at_error.to_dict())
    request.set("apitoolkit_errors", errors)
