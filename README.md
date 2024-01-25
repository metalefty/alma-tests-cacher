# AlmaLinux tests cacher

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/maccelf/809b43cccaf8256b03fc0103e245eefc/raw/alma-tests-cacher-badge__main.json)

Tool for caching third-party tests for ALTS from git repositories.

## Requirements

* git >= 2.41.0
* python >= 3.7
* aiohttp >= 3.8.6
* pydantic >= 2.5.0
* pydantic-settings >= 2.1.0
* sentry-sdk >= 1.35.0
* PyYAML >= 6.0.1
* plumbum >= 1.8.2

## Getting started

1. Create a Python Virtual Environment: `python -m venv env`
2. Activate the Virtual Environment: `source env/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `vars.yaml` file
```yaml
---
requests_limit: 5
sleep_timeout: 600
albs_api_url: http://web_server:8000
albs_jwt_token:
logging_level: DEBUG
cacher_sentry_environment: dev
cacher_sentry_dsn:
cacher_sentry_traces_sample_rate: 0.2
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
