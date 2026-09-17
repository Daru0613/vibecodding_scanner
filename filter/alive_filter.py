from core.models import FetchResult


def is_analyzable(result: FetchResult) -> bool:
    return 200 <= result.status < 400 and "html" in result.content_type.lower() and bool(result.body)

