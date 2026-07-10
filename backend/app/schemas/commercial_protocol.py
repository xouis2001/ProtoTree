from datetime import datetime

from pydantic import BaseModel


class CommercialProtocolRead(BaseModel):
    id: str
    title: str
    manufacturer: str = ""
    catalog_no: str = ""
    description: str = ""
    filename: str
    file_size: int
    author_id: int | None = None
    author_name: str = ""
    preview_url: str
    download_url: str
    star_count: int = 0
    starred_by_me: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
