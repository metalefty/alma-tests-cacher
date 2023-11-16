import pytest

from alma_tests_cacher.cacher import AlmaTestsCacher
from alma_tests_cacher.models import Config


@pytest.fixture
def config():
    yield Config()


def test_cacher_init(config: Config):
    cacher = AlmaTestsCacher(
        requests_limit=config.requests_limit,
        sleep_timeout=config.sleep_timeout,
        bs_api_url=config.bs_api_url,
        bs_jwt_token=config.bs_jwt_token,
    )
    assert isinstance(cacher, AlmaTestsCacher)
