from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1", tags=["stubs"])

def stub_response():
    raise HTTPException(status_code=501, detail="Not Implemented - Scheduled for a future phase")

# Phase 4, 5, 6 stubs removed

# Phase 8 (Implemented)

# Phase 9
@router.post("/billing/checkout")
def checkout(): stub_response()

@router.post("/billing/portal")
def portal(): stub_response()
