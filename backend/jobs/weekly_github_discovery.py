from __future__ import annotations

import asyncio
import logging

from backend.services.github_weekly_automation import GitHubWeeklyAutomationService, automation_enabled

logger = logging.getLogger(__name__)


async def main() -> None:
    if not automation_enabled():
        logger.info("GitHub weekly automation is disabled")
        return
    summary = await GitHubWeeklyAutomationService().run_once()
    logger.info(
        "GitHub weekly automation finished: status=%s checked=%s new=%s updated=%s candidates=%s emails=%s errors=%s",
        summary.get("status"),
        summary.get("repositories_checked"),
        summary.get("new_repositories_detected"),
        summary.get("updated_repositories_detected"),
        summary.get("candidates_created_or_updated"),
        summary.get("emails_sent"),
        len(summary.get("errors") or []),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(main())
