from pydantic import BaseModel


class ApiCallLogOut(BaseModel):
    id: int
    api_id: int | None = None
    method: str
    path: str
    request_body: str = ""
    response_status: int = 200
    response_body: str = ""
    duration_ms: float = 0
    error: str = ""
    user_id: int | None = None
    client_ip: str = ""
    created_at: str = ""

    model_config = {"from_attributes": True}
