from pydantic import BaseModel

class CheckoutRequest(BaseModel):
    price_id: str

class CheckoutResponse(BaseModel):
    url: str

class PortalRequest(BaseModel):
    return_url: str

class PortalResponse(BaseModel):
    url: str
