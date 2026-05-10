import os
import uuid
import logging
from typing import Protocol, Dict, Any
from db.models.integrations import IntegrationEvent

logger = logging.getLogger(__name__)

class PushChannel(Protocol):
    async def send(self, recipient: str, message: str, context: Any) -> dict[str, Any]:
        ...

class EmailChannel:
    async def send(self, recipient: str, message: str, context: Any) -> dict[str, Any]:
        # Using the same logic as email.send for abstraction
        from db.models.integrations import Integration
        from sqlalchemy import select
        from datetime import datetime, timezone

        stmt = select(Integration).where(
            Integration.tenant_id == uuid.UUID(context.tenant_id),
            Integration.kind.in_(["gmail", "outlook"])
        ).limit(1)
        
        integration = context.session.scalar(stmt)
        if not integration:
            integration = Integration(
                tenant_id=uuid.UUID(context.tenant_id),
                kind="gmail",
                connected_at=datetime.now(timezone.utc),
                status="connected"
            )
            context.session.add(integration)
            context.session.flush()

        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = context.integration_tokens.get("nylas_grant_id")
        
        kind = "email_draft"
        nylas_message_id = None
        error_msg = None
        
        # Derive subject from first line if brief
        subject = "Proactive Milo Alert"
        lines = message.strip().split("\n")
        if lines:
            first_line = lines[0].replace("#", "").strip()
            if len(first_line) > 0 and len(first_line) < 80:
                subject = first_line

        if nylas_api_key and grant_id:
            from nylas import Client
            nylas = Client(nylas_api_key)
            try:
                msg = nylas.messages.send(
                    identifier=grant_id,
                    request_body={
                        "to": [{"email": recipient}],
                        "from_": [{"name": "Milo", "email": os.environ.get("NYLAS_EMAIL", "info@scott-s-organization.nylas.email")}],
                        "reply_to": [{"name": "Milo", "email": os.environ.get("NYLAS_EMAIL", "info@scott-s-organization.nylas.email")}],
                        "subject": subject,
                        "body": message
                    }
                )
                kind = "email_sent"
                nylas_message_id = msg.data.id if hasattr(msg, 'data') else getattr(msg, 'id', None)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Nylas Send Failed: {error_msg}")
                
        draft = IntegrationEvent(
            tenant_id=uuid.UUID(context.tenant_id),
            integration_id=integration.id,
            kind=kind,
            error=error_msg,
            payload_jsonb={
                "to": recipient,
                "subject": subject,
                "body": message,
                "nylas_message_id": nylas_message_id
            }
        )
        context.session.add(draft)
        context.session.commit()
        
        if kind == "email_draft":
            return {"status": "draft", "message_id": str(draft.id), "error": "Nylas credentials missing, saved as draft."}
        return {"status": "sent", "message_id": nylas_message_id or str(draft.id)}

class NotificationManager:
    def __init__(self):
        self.channels: Dict[str, PushChannel] = {
            "email": EmailChannel()
        }
        
    async def notify(self, recipient: str, message: str, context: Any, channel_name: str = "email") -> dict[str, Any]:
        channel = self.channels.get(channel_name)
        if not channel:
            return {"error": f"Channel {channel_name} not supported."}
        return await channel.send(recipient, message, context)

manager = NotificationManager()
