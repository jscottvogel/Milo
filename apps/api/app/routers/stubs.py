from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1", tags=["stubs"])

def stub_response():
    raise HTTPException(status_code=501, detail="Not Implemented - Scheduled for a future phase")

# Phase 6
@router.get("/programs")
def get_programs(): stub_response()

@router.post("/programs")
def create_program(): stub_response()

# Phase 4
@router.get("/approvals")
def get_approvals(): stub_response()

@router.post("/approvals/{id}/decide")
def decide_approval(): stub_response()

# Phase 5
@router.patch("/milos/{id}/autonomy")
def update_autonomy(): stub_response()

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
