import uuid
from typing import Any

from pydantic import BaseModel, Field

from db.models.integrations import IntegrationEvent
from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class EmailSendInput(BaseModel):
    to: str = Field(description="The email address to send the draft to")
    subject: str = Field(description="The subject line of the email")
    body: str = Field(description="The body of the email")


class EmailSendOutput(BaseModel):
    status: str = Field(description="Status of the email delivery (e.g. 'sent')")
    message_id: str = Field(description="The internal DB ID of the sent email or persisted draft row")
    nylas_message_id: str | None = Field(default=None, description="The confirmation ID from Nylas confirming actual dispatch")


class EmailSendTool(Tool):
    name = "email.send"
    description = "Send an email. If the integration is offline or unconfigured, this safely falls back to saving it as a draft."
    input_schema = EmailSendInput
    output_schema = EmailSendOutput
    mutates = True
    requires_approval = True

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        # We store the draft as an IntegrationEvent with kind='email_draft'
        # In a real system, integration_id would be looked up based on active email integrations.
        # For the PoC draft tool, we can use a placeholder integration_id or allow it to be null
        # Wait, integration_id is not nullable in IntegrationEvent.
        # We need an active integration. For now, we will look up any active email integration,
        # or we create a dummy one if none exists (for testing purposes).
        from db.models.integrations import Integration
        from sqlalchemy import select

        stmt = select(Integration).where(
            Integration.tenant_id == uuid.UUID(context.tenant_id),
            Integration.kind.in_(["gmail", "outlook"])
        ).limit(1)
        
        integration = context.session.scalar(stmt)
        if not integration:
            # For the PoC, we will auto-create a dummy gmail integration if none exists
            from datetime import datetime, timezone
            integration = Integration(
                tenant_id=uuid.UUID(context.tenant_id),
                kind="gmail",
                connected_at=datetime.now(timezone.utc),
                status="connected"
            )
            context.session.add(integration)
            context.session.flush()

        import os
        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = context.integration_tokens.get("nylas_grant_id")
        
        kind = "email_draft"
        nylas_message_id = None
        
        error_msg = None
        if nylas_api_key and grant_id:
            from nylas import Client
            nylas = Client(nylas_api_key)
            try:
                message = nylas.messages.send(
                    identifier=grant_id,
                    request_body={
                        "to": [{"email": input_data["to"]}],
                        "from_": [{"name": "Milo", "email": os.environ.get("NYLAS_EMAIL", "info@scott-s-organization.nylas.email")}],
                        "reply_to": [{"name": "Milo", "email": os.environ.get("NYLAS_EMAIL", "info@scott-s-organization.nylas.email")}],
                        "subject": input_data["subject"],
                        "body": input_data["body"]
                    }
                )
                kind = "email_sent"
                nylas_message_id = message.data.id if hasattr(message, 'data') else getattr(message, 'id', None)
            except Exception as e:
                import logging
                error_msg = str(e)
                logging.getLogger(__name__).error(f"Nylas Send Failed: {error_msg}")
                print(f"Nylas Send Failed: {error_msg}")
                return {"error": f"Nylas API failed to send the email: {error_msg}"}
                
        draft = IntegrationEvent(
            tenant_id=uuid.UUID(context.tenant_id),
            integration_id=integration.id,
            kind=kind,
            error=error_msg,
            payload_jsonb={
                "to": input_data["to"],
                "subject": input_data["subject"],
                "body": input_data["body"],
                "nylas_message_id": nylas_message_id
            }
        )
        context.session.add(draft)
        context.session.commit()

        if kind == "email_draft":
            return {"message": "Email saved as draft because Nylas credentials (NYLAS_API_KEY or nylas_grant_id) are missing. It was NOT sent.", "draft_id": str(draft.id)}
        return EmailSendOutput(
            status="sent",
            message_id=str(draft.id),
            nylas_message_id=nylas_message_id
        ).model_dump()


class EmailReadInput(BaseModel):
    query: str = Field(default="UNSEEN", description="IMAP search query (e.g. UNSEEN, FROM sender@example.com). Defaults to UNSEEN.")
    limit: int = Field(default=10, description="Maximum number of emails to return")
    mark_read: bool = Field(default=False, description="Whether to mark the fetched emails as read")
    folder: str = Field(default="INBOX", description="The folder/mailbox to query (e.g. INBOX, Sent, [Gmail]/Sent Mail)")


class EmailReadOutput(BaseModel):
    emails: list[dict[str, Any]]


class EmailReadTool(Tool):
    name = "email.read"
    description = "Fetch emails from the connected inbox. Returns id, from, to, subject, body, timestamp, thread_id, read_status."
    input_schema = EmailReadInput
    output_schema = EmailReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        query = input_data.get("query", "UNSEEN")
        limit = min(input_data.get("limit", 10), 50)
        mark_read = input_data.get("mark_read", False)
        folder = input_data.get("folder", "INBOX")
        
        # Check for Nylas credentials
        import os
        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = context.integration_tokens.get("nylas_grant_id")
        
        # Check for IMAP credentials
        email_password = context.integration_tokens.get("email_password")
        email_user = context.integration_tokens.get("email_user")
        
        emails = []
        if nylas_api_key and grant_id:
            # NYLAS API MODE
            from nylas import Client
            nylas = Client(nylas_api_key)
            
            try:
                from typing import cast, Any
                query_params = cast(Any, {"limit": limit})
                if "UNSEEN" in query:
                    query_params["unread"] = True
                if folder.lower() != "inbox":
                    query_params["in"] = folder
                
                response = nylas.messages.list(identifier=grant_id, query_params=query_params)
                messages = response[0]
                
                for msg in messages:
                    emails.append({
                        "id": msg.id,
                        "from": msg.from_[0].get("email", "unknown") if msg.from_ and isinstance(msg.from_[0], dict) else getattr(msg.from_[0], "email", "unknown") if msg.from_ else "unknown",
                        "to": msg.to[0].get("email", "unknown") if msg.to and isinstance(msg.to[0], dict) else getattr(msg.to[0], "email", "unknown") if msg.to else "unknown",
                        "subject": msg.subject,
                        "body": msg.snippet,
                        "timestamp": msg.date,
                        "thread_id": msg.thread_id,
                        "read_status": "unread" if msg.unread else "read"
                    })
                    
                    if mark_read and msg.unread:
                        nylas.messages.update(identifier=grant_id, message_id=msg.id, request_body={"unread": False})
                        
            except Exception as e:
                return {"error": f"Nylas API Error: {str(e)}"}
        elif email_password and email_user:
            # REAL IMAP MODE
            import imaplib
            import email
            from email.header import decode_header
            
            try:
                # Assume standard IMAP SSL port and guess server
                imap_server = "imap.mail.yahoo.com" if "yahoo.com" in email_user else "imap.gmail.com"
                mail = imaplib.IMAP4_SSL(imap_server)
                mail.login(email_user, email_password)
                mail.select(f'"{folder}"')
                
                status, messages = mail.search(None, query)
                if status == "OK":
                    msg_nums = messages[0].split()
                    # Get the most recent emails up to limit
                    msg_nums = msg_nums[-limit:]
                    
                    for num in msg_nums:
                        status, data = mail.fetch(num, '(RFC822)')
                        if status == "OK" and data and data[0]:
                            raw_email = data[0][1]
                            if isinstance(raw_email, bytes):
                                msg = email.message_from_bytes(raw_email)
                            else:
                                continue
                            
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")
                                
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))
                                    
                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        body = part.get_payload(decode=True)
                                        if isinstance(body, bytes):
                                            body = body.decode()
                                        break
                            else:
                                body = msg.get_payload(decode=True)
                                if isinstance(body, bytes):
                                    body = body.decode()
                                
                            body_str = str(body) if body else ""
                            emails.append({
                                "id": msg.get("Message-ID", ""),
                                "from": msg.get("From", ""),
                                "to": msg.get("To", ""),
                                "subject": subject,
                                "body": body_str[:2000], # truncate long emails
                                "timestamp": msg.get("Date", ""),
                                "thread_id": msg.get("In-Reply-To", msg.get("Message-ID", "")),
                                "read_status": "read" if mark_read else "unread"
                            })
                        
                        if mark_read:
                            mail.store(num, '+FLAGS', '\\Seen')
                            
                mail.close()
                mail.logout()
            except Exception as e:
                return {"error": f"IMAP Error: {str(e)}"}
        else:
            # DATABASE MOCK MODE
            from sqlalchemy import select
            
            if folder.lower() == "inbox":
                stmt = select(IntegrationEvent).where(
                    IntegrationEvent.tenant_id == uuid.UUID(context.tenant_id),
                    IntegrationEvent.kind == "email_received",
                    IntegrationEvent.status == "pending"
                ).order_by(IntegrationEvent.created_at.desc()).limit(limit)
            else:
                stmt = select(IntegrationEvent).where(
                    IntegrationEvent.tenant_id == uuid.UUID(context.tenant_id),
                    IntegrationEvent.kind == "email_sent"
                ).order_by(IntegrationEvent.created_at.desc()).limit(limit)
            
            events = context.session.scalars(stmt).all()
            for event in events:
                payload = event.payload_jsonb or {}
                # check query if it's not strictly UNSEEN
                if "FROM" in query and payload.get("from") not in query:
                    continue
                    
                emails.append({
                    "id": str(event.id),
                    "from": payload.get("from", "unknown@example.com"),
                    "to": payload.get("to", "milo@example.com"),
                    "subject": payload.get("subject", "No Subject"),
                    "body": payload.get("body", ""),
                    "timestamp": event.created_at.isoformat() if hasattr(event, "created_at") and event.created_at else None,
                    "thread_id": payload.get("thread_id", str(event.id)),
                    "read_status": "unread"
                })
                
                if mark_read:
                    event.status = "processed"
                    context.session.add(event)
                    
            if mark_read:
                context.session.commit()
                
        return EmailReadOutput(emails=emails).model_dump()
