from fastapi import APIRouter, Request
import uuid
from schemas.billing import CheckoutRequest, CheckoutResponse, PortalRequest, PortalResponse

router = APIRouter(prefix="/v1/billing", tags=["billing"])

@router.post("/checkout", response_model=CheckoutResponse)
def checkout(request: Request, payload: CheckoutRequest):
    """
    Returns a mock Stripe Checkout URL for the requested plan.
    """
    tenant_id = request.state.auth_context.tenant_id
    mock_session_id = f"cs_test_{uuid.uuid4().hex[:16]}"
    return CheckoutResponse(
        url=f"https://checkout.stripe.com/pay/{mock_session_id}"
    )

@router.post("/portal", response_model=PortalResponse)
def portal(request: Request, payload: PortalRequest):
    """
    Returns a mock Stripe Customer Portal URL.
    """
    tenant_id = request.state.auth_context.tenant_id
    mock_session_id = f"pts_test_{uuid.uuid4().hex[:16]}"
    return PortalResponse(
        url=f"https://billing.stripe.com/p/session/{mock_session_id}"
    )
