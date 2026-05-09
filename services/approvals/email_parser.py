import re
import logging
from sqlalchemy.orm import Session
from .models import Approval
from .notifier import send_confirmation_email

logger = logging.getLogger(__name__)

def parse_inbound_email(payload: dict, db: Session):
    """
    Parses inbound Nylas webhook payload to extract approval decision.
    """
    try:
        # Structure varies by webhook version, assuming standard message.created
        message_data = payload.get("data", {}).get("object", {})
        if not message_data:
            return

        subject = message_data.get("subject", "")
        body = message_data.get("snippet", "") or message_data.get("body", "")
        sender_email = ""
        if message_data.get("from"):
            sender_email = message_data["from"][0].get("email", "")

        # 1. Extract Approval ID from Subject or Body
        # Look for a UUID in the body or subject
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, subject + " " + body, re.IGNORECASE)
        
        if not match:
            logger.warning("No approval ID found in inbound email.")
            return
            
        approval_id = match.group(0)
        
        # 2. Extract Decision
        # Look for APPROVE, REJECT, DELEGATE, DEFER at the start of the reply
        decision = None
        for word in ["APPROVE", "REJECT", "DELEGATE", "DEFER"]:
            if word.lower() in body.lower():
                decision = word.lower()
                # Use the first one found or enhance logic to ensure it's at the top
                break
                
        if not decision:
            logger.warning(f"No valid decision found for approval {approval_id}")
            return

        # 3. Update DB
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            logger.warning(f"Approval {approval_id} not found in DB.")
            return
            
        if approval.status != "pending":
            logger.info(f"Approval {approval_id} already processed.")
            return

        if decision not in approval.options:
            logger.warning(f"Decision {decision} not in valid options {approval.options}")
            return

        approval.status = decision
        if decision == "approve":
            approval.status = "approved"
        elif decision == "reject":
            approval.status = "rejected"
        elif decision == "delegate":
            approval.status = "delegated"
        elif decision == "defer":
            approval.status = "deferred"
            
        approval.decision = decision
        approval.decided_by = sender_email
        from datetime import datetime, timezone
        approval.decided_at = datetime.now(timezone.utc)
        approval.notes = body[:500] # Store snippet as notes
        
        db.commit()
        logger.info(f"Successfully processed inbound decision {decision} for {approval_id}")

        # 4. Send confirmation
        import asyncio
        asyncio.create_task(
            send_confirmation_email(str(approval.id), approval.title, approval.status, sender_email)
        )

    except Exception as e:
        logger.error(f"Error parsing inbound email: {e}")
