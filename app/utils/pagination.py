from typing import Tuple

from flask import current_app, request


def get_pagination() -> Tuple[int, int]:
    """Read ?page= and ?per_page= with sane bounds (page >= 1, 1 <= per_page <= MAX_PAGE_SIZE)."""
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = request.args.get("per_page", current_app.config["PAGE_SIZE"], type=int)
    per_page = min(max(per_page, 1), current_app.config["MAX_PAGE_SIZE"])
    return page, per_page


def page_info(total: int, page: int, per_page: int) -> dict:
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
