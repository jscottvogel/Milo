import json
from sqlalchemy import select
from db.session import SessionLocal
from db.models.program import ProgramStakeholder

def lambda_handler(event, context):
    """
    Cognito Pre-Token-Generation Trigger for milo-stakeholder-pool.
    Retrieves active tenant and program memberships and injects them as custom claims.
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Extract the user sub (this is the stakeholder identity)
    request = event.get('request', {})
    user_attributes = request.get('userAttributes', {})
    sub = user_attributes.get('sub')
    
    if not sub:
        return event

    memberships = []

    try:
        # Use a raw session to bypass RLS, since this is a global auth resolution step
        with SessionLocal() as session:
            stmt = select(ProgramStakeholder).where(
                ProgramStakeholder.stakeholder_sub == sub,
                ProgramStakeholder.status == 'active'
            )
            results = session.execute(stmt).scalars().all()
            
            for row in results:
                memberships.append({
                    "tenant_id": str(row.tenant_id),
                    "program_id": str(row.program_id),
                    "role": row.role
                })
    except Exception as e:
        print(f"Error fetching stakeholder memberships: {e}")
        # Fail open with no memberships, API Gateway Authorizer will reject access
        pass

    # Inject the custom claim
    # Cognito requires custom claims to be stringified JSON if it's an array/object
    event['response'] = {
        'claimsOverrideDetails': {
            'claimsToAddOrOverride': {
                'custom:tenant_memberships': json.dumps(memberships)
            }
        }
    }
    
    return event
