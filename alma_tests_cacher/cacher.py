import asyncio
import logging
import re
import urllib.parse
from typing import List, Optional, Union

import aiohttp

from alma_tests_cacher.constants import (
    DEFAULT_BS_API_URL,
    DEFAULT_LOGGING_LEVEL,
    DEFAULT_REQUESTS_LIMIT,
    DEFAULT_SLEEP_TIMEOUT,
)
from alma_tests_cacher.models import PackageTestRepository, TestRepository


class AlmaTestsCacher:
    def __init__(
        self,
        bs_jwt_token: str = '',
        requests_limit: int = DEFAULT_REQUESTS_LIMIT,
        sleep_timeout: int = DEFAULT_SLEEP_TIMEOUT,
        bs_api_url: str = DEFAULT_BS_API_URL,
        logging_level: str = DEFAULT_LOGGING_LEVEL,
    ):
        self.requests_limit = asyncio.Semaphore(requests_limit)
        self.sleep_timeout = sleep_timeout
        self.bs_api_url = bs_api_url
        self.bs_headers = {
            "Authorization": f"Bearer {bs_jwt_token}",
        }
        self.bs_jwt_token = bs_jwt_token
        self.session_mapping = {}
        self.logger = self.setup_logger(logging_level)

    def setup_logger(self, logging_level: str) -> logging.Logger:
        logger = logging.getLogger('tests-cacher')
        logger.setLevel(logging_level)
        handler = logging.StreamHandler()
        handler.setLevel(logging_level)
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s:%(levelname)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def close_sessions(self):
        self.logger.debug('Closing active HTTP sessions')
        for url, session in self.session_mapping.items():
            try:
                self.logger.debug('Closing HTTP session for %s', url)
                await session.close()
                self.logger.debug('HTTP session for %s is closed', url)
            except Exception:
                self.logger.exception('Cannot close HTTP session for %s:', url)
        self.session_mapping = {}

    def get_session(self, base_url: str) -> aiohttp.ClientSession:
        if base_url not in self.session_mapping:
            session = aiohttp.ClientSession(base_url)
            self.session_mapping[base_url] = session
            return session
        return self.session_mapping[base_url]

    async def make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[dict] = None,
        return_text: bool = False,
        json: Optional[Union[dict, List[int], List[dict]]] = None,
    ) -> Union[str, dict]:
        self.logger.debug('Making new request %s', endpoint)
        async with self.requests_limit:
            parsed_url = urllib.parse.urlsplit(endpoint)
            session = self.get_session(
                f'{parsed_url.scheme}://{parsed_url.netloc}',
            )
            async with session.request(
                method=method.lower(),
                url=parsed_url.path,
                headers=headers,
                json=json,
            ) as response:
                response.raise_for_status()
                if return_text:
                    return await response.text()
                return await response.json()

    async def get_test_repositories(self) -> List[TestRepository]:
        test_repos = []
        try:
            response = await self.make_request(
                method='get',
                endpoint=urllib.parse.urljoin(
                    self.bs_api_url,
                    '/api/v1/test_repositories/',
                ),
                headers=self.bs_headers,
            )
        except Exception:
            self.logger.exception('Cannot get test repositories:')
            return test_repos
        for test_repo in response:
            test_repos.append(TestRepository(**test_repo))
        return test_repos

    async def bulk_remove_test_folders(
        self,
        test_folders_ids: List[int],
        repository_id: int,
    ):
        if not test_folders_ids:
            return
        try:
            await self.make_request(
                endpoint=urllib.parse.urljoin(
                    self.bs_api_url,
                    f'/api/v1/test_repositories/{repository_id}/packages/bulk_remove/',
                ),
                method='post',
                headers=self.bs_headers,
                json=test_folders_ids,
            )
        except Exception:
            self.logger.exception('Cannot remove existing test folders:')

    async def bulk_create_test_folders(
        self,
        test_folders: List[PackageTestRepository],
        repository_id: int,
    ):
        if not test_folders:
            return
        try:
            await self.make_request(
                endpoint=urllib.parse.urljoin(
                    self.bs_api_url,
                    f'/api/v1/test_repositories/{repository_id}/packages/bulk_create/',
                ),
                method='post',
                json=[test_folder.dict() for test_folder in test_folders],
                headers=self.bs_headers,
            )
        except Exception:
            self.logger.exception('Cannot create new test folders:')

    async def get_test_repo_content(self, url: str) -> str:
        repo_content = ''
        try:
            repo_content = await self.make_request(
                method='get',
                endpoint=url,
                return_text=True,
            )
        except Exception:
            self.logger.exception('Cannot get repo content:')
        return repo_content

    async def process_repo(
        self,
        db_repo: TestRepository,
    ):
        async with self.requests_limit:
            remote_test_folders = []
            new_test_folders = []
            tests_prefix = db_repo.tests_prefix if db_repo.tests_prefix else ''
            self.logger.info('Start processing "%s" repo', db_repo.name)
            repo_content = await self.get_test_repo_content(
                urllib.parse.urljoin(db_repo.url, db_repo.tests_dir),
            )
            for line in repo_content.splitlines():
                result = re.search(
                    rf'href="({tests_prefix}.+)"',
                    line,
                )
                if not result:
                    continue
                remote_test_folders.append(result.groups()[0])
            test_folders_mapping = {
                test.folder_name: test for test in db_repo.packages
            }
            for remote_test_folder in remote_test_folders:
                db_test = test_folders_mapping.get(remote_test_folder)
                if db_test:
                    continue
                new_test = PackageTestRepository(
                    folder_name=remote_test_folder,
                    package_name=re.sub(
                        rf'^{tests_prefix}',
                        '',
                        remote_test_folder,
                    ),
                    url=urllib.parse.urljoin(
                        urllib.parse.urljoin(db_repo.url, db_repo.tests_dir),
                        remote_test_folder,
                    ),
                )
                new_test_folders.append(new_test)
                db_repo.packages.append(new_test)
            await self.bulk_create_test_folders(new_test_folders, db_repo.id)
            await self.bulk_remove_test_folders(
                [
                    db_test.id
                    for db_test in db_repo.packages
                    if db_test.folder_name not in remote_test_folders
                    and db_test.id
                ],
                db_repo.id,
            )
            if not remote_test_folders and db_repo.packages:
                await self.bulk_remove_test_folders(
                    [db_test.id for db_test in db_repo.packages if db_test.id],
                    db_repo.id,
                )
            self.logger.info('Repo "%s" is processed', db_repo.name)

    async def run(self, dry_run: bool = False):
        while True:
            self.logger.info('Start processing test repositories')
            try:
                db_repos = await self.get_test_repositories()
                await asyncio.gather(
                    *(self.process_repo(db_repo) for db_repo in db_repos)
                )
            except Exception:
                self.logger.exception('Cannot process test repositories:')
            finally:
                await self.close_sessions()
            self.logger.info(
                'All repositories are processed, sleeping %d seconds',
                self.sleep_timeout,
            )
            await asyncio.sleep(self.sleep_timeout)
            if dry_run:
                break
