import json
from pathlib import Path
from typing import Any, Dict

import pytest

from alma_tests_cacher.cacher import AlmaTestsCacher
from alma_tests_cacher.models import Config, TestRepository
from alma_tests_cacher.utils import get_config


@pytest.fixture
def default_vars() -> str:
    return """
    sleep_timeout: 0
    """


@pytest.fixture
def config(tmp_path: Path, default_vars: str) -> Config:
    conf_path = Path(tmp_path, 'vars.yaml')
    conf_path.write_text(default_vars)
    return get_config(config_path=conf_path)


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture
def cacher(config: Config) -> AlmaTestsCacher:
    return AlmaTestsCacher(
        requests_limit=config.requests_limit,
        sleep_timeout=0,
        bs_api_url=config.bs_api_url,
        bs_jwt_token=config.bs_jwt_token,
        gerrit_username=config.gerrit_username,
    )


@pytest.fixture
def repo_payload() -> TestRepository:
    return TestRepository(
        id=1,
        name='test-repo',
        url='git@github.com:anfimovdm/third-party-tests.git',
        tests_dir='rpm_tests/',
        tests_prefix='p_',
        packages=[],
    )


@pytest.fixture
def expected_payload() -> Dict[str, Any]:
    return {
        'repo_id': 1,
        'test_repos': [
            {
                'id': None,
                'package_name': 'chan',
                'folder_name': 'p_chan',
                'url': 'git@github.com:anfimovdm/rpm_tests/p_chan',
            },
            {
                'id': None,
                'package_name': 'common',
                'folder_name': 'common',
                'url': 'git@github.com:anfimovdm/rpm_tests/common',
            },
        ],
    }


def test_config(config: Config):
    for assert_expr in (
        isinstance(config, Config),
        config.sleep_timeout == 0,
    ):
        assert assert_expr


def test_cacher_init(cacher: AlmaTestsCacher):
    assert isinstance(cacher, AlmaTestsCacher)


@pytest.fixture
def mock_get_test_repos(
    monkeypatch: pytest.MonkeyPatch,
    repo_payload: TestRepository,
):
    async def func(*args, **kwargs):
        return [repo_payload]

    monkeypatch.setattr(AlmaTestsCacher, 'get_test_repositories', func)


@pytest.fixture
def mock_bulk_remove(monkeypatch: pytest.MonkeyPatch):
    async def func(*args, **kwargs):
        return

    monkeypatch.setattr(AlmaTestsCacher, 'bulk_remove_test_folders', func)


@pytest.fixture
def mock_bulk_create(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    async def func(*args, **kwargs):
        _, test_repos, repo_id = args
        test_repos = [repo.model_dump() for repo in test_repos]
        Path(tmp_path, 'create_payload.json').write_text(
            json.dumps({'repo_id': repo_id, 'test_repos': test_repos}),
        )
        return

    monkeypatch.setattr(AlmaTestsCacher, 'bulk_create_test_folders', func)


@pytest.mark.anyio
@pytest.mark.usefixtures(
    'mock_get_test_repos',
    'mock_bulk_create',
    'mock_bulk_remove',
)
async def test_cacher_run(
    cacher: AlmaTestsCacher,
    tmp_path: Path,
    expected_payload: Dict[str, Any],
):
    await cacher.run(dry_run=True)
    payload = json.loads(Path(tmp_path, 'create_payload.json').read_text())
    for assert_expr in (
        payload['repo_id'] == expected_payload['repo_id'],
        payload['test_repos'] == payload['test_repos'],
    ):
        assert assert_expr
