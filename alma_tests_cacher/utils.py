from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

import yaml
from plumbum import local

from alma_tests_cacher.constants import DEFAULT_CONFIG_PATH
from alma_tests_cacher.models import Config


def get_config(config_path: Optional[Path] = None) -> Config:
    with open(config_path or DEFAULT_CONFIG_PATH, 'rt') as file:
        return Config.model_validate(yaml.safe_load(file))


def prepare_gerrit_repo_url(url: str, username: str) -> str:
    parsed = urlparse(url)
    return urlunparse(
        (
            parsed.scheme,
            f'{username}@{parsed.netloc}',
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def clone_git_repo(
    workdir_path: str,
    repo_url: str,
) -> Tuple[int, str, str]:
    return (
        local['git']
        .with_cwd(workdir_path)
        .run(
            ['clone', repo_url],
            retcode=None,
        )
    )


def git_pull(
    workdir_path: str,
    branch: str = 'master',
) -> Tuple[int, str, str]:
    return (
        local['git']
        .with_cwd(workdir_path)
        .run(
            ['pull', 'origin', branch],
            retcode=None,
        )
    )
