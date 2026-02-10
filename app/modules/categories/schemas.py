from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    parent_id: int | None = None
    icon: str | None = None
    color: str | None = None


class CategoryRead(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    icon: str | None = None
    color: str | None = None

    class Config:
        from_attributes = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    icon: str | None = None
    color: str | None = None


class CategoryListResponse(BaseModel):
    items: list[CategoryRead]
    total: int
    skip: int
    limit: int
