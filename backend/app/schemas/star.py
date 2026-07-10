from pydantic import BaseModel


class ProtocolStarSummary(BaseModel):
    protocol_id: int
    star_count: int
    starred_by_me: bool
