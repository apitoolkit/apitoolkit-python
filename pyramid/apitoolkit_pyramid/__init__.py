import json
import uuid
from urllib.parse import urlsplit
from opentelemetry.trace import get_tracer
from pyramid.request import Request
from common import observe_request, report_error, set_attributes


observe_request = observe_request
report_error = report_error

OPTIONAL_SETTINGS = (
    # var in class, environment name, type, default value
    ('debug', 'APITOOLKIT_DEBUG', bool, False),
    ('service_name', 'SERVICE_NAME', str, None),
    ('capture_request_body', 'APITOOLKIT_CAPTURE_REQ_BODY', bool, False),
    ('capture_response_body', 'APITOOLKIT_CAPTURE_RES_BODY', bool, False),
    ('redact_headers', 'APITOOLKIT_REDACT_HEADERS', list, []),
    ('redact_request_body', 'APITOOLKIT_REDACT_REQ_BODY', list, []),
    ('redact_response_body', 'APITOOLKIT_REDACT_RES_BODY', list, []),
    ('routes_whitelist', 'APITOOLKIT_ROUTES_WHITELIST', list, []),
    ('ignore_http_codes', 'APITOOLKIT_IGNORE_HTTP_CODES', list, []),
    ('service_version', 'APITOOLKIT_SERVICE_VERSION', str, None),
    ('tags', 'APITOOLKIT_TAGS', list, []),
)


class APIToolkit(object):
    def __init__(self, handler, registry):
        self.get_response = handler
        for var_name, env_id, _type, default in OPTIONAL_SETTINGS:
            self.prepare_optional_settings(var_name, registry.settings.get(env_id), _type, default)
        self.config = {
            'service_name': self.service_name,
            'service_version': self.service_version,
            'debug': self.debug,
            'capture_request_body': self.capture_request_body,
            'capture_response_body': self.capture_response_body,
            'redact_headers': self.redact_headers,
            'redact_request_body': self.redact_request_body,
            'redact_response_body': self.redact_response_body,
            'routes_whitelist': self.routes_whitelist,
            'ignore_http_codes': self.ignore_http_codes,
            'tags': self.tags,
        }

    def prepare_optional_settings(self, var_name, value, _type, default):
        if _type in (bool, str):
            setattr(self, var_name, value or default)
        elif _type is list:
            # env value can directly be a list or when given via ini file a comma separated string
            try:
                setattr(self, var_name, value.split(','))
            except AttributeError:
                setattr(self, var_name, value or [])

    def process_exception(self, request, exception):
        report_error(request,exception)
        pass

    def __call__(self, request: Request):
        tracer = get_tracer(self.service_name)
        span = tracer.start_span("apitoolkit-http-span")
        if self.debug:
            print("APIToolkit: making request")

        request.apitoolkit_message_id = str(uuid.uuid4())
        request.apitoolkit_errors = []

        response = self.get_response(request)
        status_code = response.status_code

        url_path = request.matched_route.pattern if request.matched_route is not None else request.path

        # return early conditions (no logging)
        if self.routes_whitelist:
            # when route does not match any of the whitelist routes
            if not any([url_path.startswith(route) for route in self.routes_whitelist]):
                return response
        if status_code in [int(code) for code in self.ignore_http_codes]:
            return response

        if self.debug:
            print("APIToolkit: after request")
        try:
            request_method = request.method
            raw_url = request.url
            parsed_url = urlsplit(raw_url)
            url_path_with_query = parsed_url.path + parsed_url.query
            request_body = None
            query_params =  {key: value for key, value in request.params.items()}
            request_headers = request.headers
            content_type = request.headers.get('Content-Type', '')

            if content_type == 'application/json':
                request_body = request.json_body
            if content_type == 'text/plain':
                request_body = request.body.decode('utf-8')
            if content_type == 'application/x-www-form-urlencoded' or 'multipart/form-data' in content_type:
                request_body = dict(request.POST.copy())

            url_path = request.matched_route.pattern if request.matched_route is not None else request.path
            path_params = request.matchdict
            request_body = json.dumps(request_body)
            response_headers = response.headers
            request_body = request_body
            response_body =  response.body
            message_id = request.apitoolkit_message_id
            errors = request.apitoolkit_errors

            set_attributes(
                span,
                request.headers.get('HOST',""),
                status_code,
                query_params,
                path_params,
                request_headers,
                response_headers,
                request_method,
                url_path_with_query,
                message_id,
                url_path,
                request_body,
                response_body,
                errors,
                self.config,
                "PythonPyramid"
            )
        except Exception as e:
            return response
        return response
