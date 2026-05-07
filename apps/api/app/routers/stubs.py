from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1", tags=["stubs"])

def stub_response():
    raise HTTPException(status_code=501, detail="Not Implemented - Scheduled for a future phase")

# Phase 4, 5, 6 stubs removed

# Phase 8
@router.get("/integrations")
def get_integrations(): stub_response()

@router.post("/integrations/gmail/connect")
def connect_gmail(): stub_response()

@router.get("/integrations/oauth/callback")
def oauth_callback(): stub_response()

# Phase 9
@router.post("/billing/checkout")
def checkout(): stub_response()

@router.post("/billing/portal")
def portal(): stub_response()
