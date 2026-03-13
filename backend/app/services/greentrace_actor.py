from typing import Any

from apify_client import ApifyClient

from app.core.config import get_settings
from app.schemas.company_esg import CompanyEsgOptions


class ActorServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def run_greentrace_actor(company: str, options: CompanyEsgOptions) -> dict[str, Any]:
    settings = get_settings()
    if not settings.apify_token:
        raise ActorServiceError("APIFY_TOKEN is not configured", status_code=500)

    client = ApifyClient(settings.apify_token)
    actor_input = {"company": company, **options.model_dump(exclude_none=True)}

    try:
        run = client.actor(settings.apify_actor_id).call(
            run_input=actor_input,
            timeout_secs=settings.apify_timeout_secs,
            wait_secs=settings.apify_timeout_secs,
        )
    except Exception as exc:
        raise ActorServiceError(f"Failed to run GreenTrace actor: {exc}") from exc

    if not run or not run.get("defaultDatasetId"):
        raise ActorServiceError("GreenTrace actor did not return a dataset")

    try:
        items = client.dataset(run["defaultDatasetId"]).list_items().items
    except Exception as exc:
        raise ActorServiceError(f"Failed to fetch actor dataset: {exc}") from exc

    if not items:
        raise ActorServiceError("GreenTrace actor returned an empty dataset", status_code=404)

    return items[0]