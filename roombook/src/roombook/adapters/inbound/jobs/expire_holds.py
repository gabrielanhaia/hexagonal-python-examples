"""The expire-holds job: cron or a Kubernetes CronJob runs it."""

import structlog

from roombook.application.expire_stale_holds import ExpireStaleHolds

log = structlog.get_logger()


async def expire_holds(expire_stale_holds: ExpireStaleHolds) -> int:
    expired = await expire_stale_holds()
    await log.ainfo("holds expired", count=expired)
    return expired
