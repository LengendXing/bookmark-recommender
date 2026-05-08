from pydantic import BaseModel


class TrustedDeviceOut(BaseModel):
    id: int
    device_name: str
    ip_address: str
    user_agent: str
    created_at: str
    last_used_at: str

    model_config = {"from_attributes": True}
