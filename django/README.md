<div align="center">

![APItoolkit's Logo](https://github.com/apitoolkit/.github/blob/main/images/logo-white.svg?raw=true#gh-dark-mode-only)
![APItoolkit's Logo](https://github.com/apitoolkit/.github/blob/main/images/logo-black.svg?raw=true#gh-light-mode-only)

## Django SDK

[![APItoolkit SDK](https://img.shields.io/badge/APItoolkit-SDK-0068ff?logo=django)](https://github.com/topics/apitoolkit-sdk) [![PyPI - Version](https://img.shields.io/pypi/v/apitoolkit-django)](https://pypi.org/project/apitoolkit-django) [![PyPI - Downloads](https://img.shields.io/pypi/dw/apitoolkit-django)](https://pypi.org/project/apitoolkit-django) [![Join Discord Server](https://img.shields.io/badge/Chat-Discord-7289da)](https://apitoolkit.io/discord?utm_campaign=devrel&utm_medium=github&utm_source=sdks_readme) [![APItoolkit Docs](https://img.shields.io/badge/Read-Docs-0068ff)](https://apitoolkit.io/docs/sdks/python/django?utm_campaign=devrel&utm_medium=github&utm_source=sdks_readme)

APIToolkit Django SDK is a middleware that can be used to monitor HTTP requests. It is provides additional functionalities on top of the open telemetry instrumentation which creates a custom span for each request capturing details about the request including request, response bodies errors and outgoing requests.

</div>

---

## Table of Contents

- [Installation](#installation)
- [Setup Open Telemetry](#setup-open-telemetry)
- [Configuration](#apitoolkit-django-configuration)
- [Contributing and Help](#contributing-and-help)
- [License](#license)

---

## Installation

Kindly run the command below to install the apitoolkit django sdks and necessary opentelemetry packages:

```sh
pip install apitoolkit-django opentelemetry-distro opentelemetry-exporter-otlp
# then install the bootstrap script
opentelemetry-bootstrap -a install
```

## Setup Open Telemetry

Setting up open telemetry allows you to send traces, metrics and logs to the APIToolkit platform.
To setup open telemetry, you need to configure the following environment variables:

```sh
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.apitoolkit.io:4317"
export OTEL_SERVICE_NAME="my-service" # Specifies the name of the service.
export OTEL_RESOURCE_ATTRIBUTES="at-project-key={ENTER_YOUR_API_KEY_HERE}" # Adds your API KEY to the resource.
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc" # Specifies the protocol to use for the OpenTelemetry exporter.
export DJANGO_SETTINGS_MODULE="{YOUR_DJANGO_SERVER_NAME}.settings" # Specifies the Django settings module to use.
```

Then run the command below to start your server with opentelemetry instrumented:

```sh
opentelemetry-instrument python3 manage.py runserver --noreload
```

## APItoolkit Django Configuration

After setting up open telemetry, you can now configure the apitoolkit django middleware.
By adding the following APItoolkit variables to your Django settings (`settings.py`) file:

```python
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

APITOOLKIT_SERVICE_NAME= "my-service"
APITOOLKIT_CAPTURE_REQUEST_BODY = True
APITOOLKIT_CAPTURE_RESPONSE_BODY = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
]

...
```

Then add the `apitoolkit_django.APIToolkit` middleware into the `settings.py` middleware list, like so:

```python
MIDDLEWARE = [
    'apitoolkit_django.APIToolkit', # Initialize APItoolkit
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...,
]
```

> [!NOTE]
>
> The `{ENTER_YOUR_API_KEY_HERE}` demo string should be replaced with the [API key](https://apitoolkit.io/docs/dashboard/settings-pages/api-keys?utm_campaign=devrel&utm_medium=github&utm_source=sdks_readme) generated from the APItoolkit dashboard.
>
> The `{YOUR_DJANGO_SERVER_NAME}` demo string should be replaced with the name of your Django server.
> <br />

> [!IMPORTANT]
>
> To learn more configuration options (redacting fields, error reporting, outgoing requests, etc.), please read this [SDK documentation](https://apitoolkit.io/docs/sdks/python/django?utm_campaign=devrel&utm_medium=github&utm_source=sdks_readme).

## Contributing and Help

To contribute to the development of this SDK or request help from the community and our team, kindly do any of the following:

- Read our [Contributors Guide](https://github.com/apitoolkit/.github/blob/main/CONTRIBUTING.md).
- Join our community [Discord Server](https://apitoolkit.io/discord?utm_campaign=devrel&utm_medium=github&utm_source=sdks_readme).
- Create a [new issue](https://github.com/apitoolkit/apitoolkit-django/issues/new/choose) in this repository.

## License

This repository is published under the [MIT](LICENSE) license.

---

<div align="center">

<a href="https://apitoolkit.io?utm_campaign=devrel&utm_medium=github&utm_source=sdks_readme" target="_blank" rel="noopener noreferrer"><img src="https://github.com/apitoolkit/.github/blob/main/images/icon.png?raw=true" width="40" /></a>

</div>
