import asyncio

import sentry_sdk

from alma_tests_cacher.cacher import AlmaTestsCacher
from alma_tests_cacher.utils import get_config


async def main():
    config = get_config()
    if config.cacher_sentry_dsn:
        sentry_sdk.init(
            dsn=config.cacher_sentry_dsn,
            traces_sample_rate=config.cacher_sentry_traces_sample_rate,
            environment=config.cacher_sentry_environment,
        )
    await AlmaTestsCacher(
        requests_limit=config.requests_limit,
        sleep_timeout=config.sleep_timeout,
        bs_api_url=config.bs_api_url,
        bs_jwt_token=config.bs_jwt_token,
        common_test_dir_name=config.common_test_dir_name,
        gerrit_username=config.gerrit_username,
    ).run()


if __name__ == '__main__':
    asyncio.run(main())
