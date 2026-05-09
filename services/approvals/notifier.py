import os
import logging
from .models import Approval

logger = logging.getLogger(__name__)

async def send_approval_email(approval: Approval):
    """
    Sends an email to notify_email with the approval details.
    Uses Nylas SDK or Nylas MCP for send.
    """
    try:
        subject = f"[Milo] Action Required: {approval.title}"
        body = f"""
        <html>
        <body>
            <h2>Approval Required: {approval.title}</h2>
            <p>{approval.description}</p>
            <p><strong>Requested By:</strong> {approval.requested_by}</p>
            <p><strong>Due By:</strong> {approval.due_by}</p>
            <hr>
            <h3>Respond</h3>
            <p>Please reply to this email with one of the following decisions as the first word:</p>
            <ul>
        """
        for opt in approval.options:
            body += f"<li><strong>{opt.upper()}</strong></li>"
        
        body += f"""
            </ul>
            <br>
            <p><i>Approval ID: {approval.id}</i></p>
        </body>
        </html>
        """

        # In a real implementation, you would fetch NYLAS_API_KEY from Secrets Manager
        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = os.environ.get("NYLAS_GRANT_ID")

        if nylas_api_key and grant_id:
            from nylas import Client
            nylas = Client(nylas_api_key)
            nylas.messages.send(
                identifier=grant_id,
                request_body={
                    "to": [{"email": approval.notify_email}],
                    "reply_to": [{"name": "Milo", "email": "milo@example.com"}],
                    "subject": subject,
                    "body": body
                }
            )
            logger.info(f"Sent approval email for {approval.id} to {approval.notify_email}")
        else:
            logger.warning("NYLAS credentials not found, skipping email send. Body would be: %s", body)

    except Exception as e:
        logger.error(f"Failed to send approval email: {e}")

async def send_confirmation_email(approval_id: str, title: str, decision: str, notify_email: str):
    """
    Sends a confirmation email after a decision is made via reply.
    """
    try:
        subject = f"[Milo] Decision Recorded: {title} -> {decision}"
        body = f"Your decision to {decision.upper()} for '{title}' has been recorded."

        nylas_api_key = os.environ.get("NYLAS_API_KEY")
        grant_id = os.environ.get("NYLAS_GRANT_ID")

        if nylas_api_key and grant_id:
            from nylas import Client
            nylas = Client(nylas_api_key)
            nylas.messages.send(
                identifier=grant_id,
                request_body={
                    "to": [{"email": notify_email}],
                    "subject": subject,
                    "body": body
                }
            )
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")
