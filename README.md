# AlmaLinux tests cacher

Tool for caching third-party tests for ALTS from git repositories.

## Requirements

* python >= 3.7
* aiohttp >= 3.8.6
* pydantic >= 2.5.0
* pydantic-settings >= 2.1.0
* sentry-sdk >= 1.35.0
* pytest >= 7.4.3

## Getting started

1. Create a Python Virtual Environment: `python -m venv env`
2. Activate the Virtual Environment: `source env/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `vars.env` file
```
REQUESTS_LIMIT="5"
SLEEP_TIMEOUT="600"
BS_API_URL="http://web_server:8000"
LOGGING_LEVEL="DEBUG"
BS_JWT_TOKEN=""
CACHER_SENTRY_ENVIRONMENT="dev"
CACHER_SENTRY_DSN=""
CACHER_SENTRY_TRACES_SAMPLE_RATE="0.2"
```

## Running the AlmaLinux tests cacher
```bash
source env/bin/activate
python alma_tests_cacher.py
```

## Contributing to the AlmaLinux tests cacher

Any question? Found a bug? File an [issue](https://github.com/AlmaLinux/alma-tests-cacher/issues).
Do you want to contribute with source code?
1. Fork the repository on GitHub
2. Create a new feature branch
3. Write your change
4. Submit a pull request
