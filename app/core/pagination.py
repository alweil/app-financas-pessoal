from dataclasses import dataclass

from fastapi import Query


@dataclass(frozen=True)
class PaginationParams:
    skip: int
    limit: int


def get_pagination_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


def paginate_query(query, skip: int, limit: int):
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total
