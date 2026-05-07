import datetime
import logging
from sqlalchemy import create_engine, select, update
from db.models.agent import Approval
from app.config import settings
from db.session import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def expire_approvals():
    logger.info("Starting expiration of stale approvals.")
    
    # We use a direct engine connection since this is a background job without tenant context
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        now = datetime.datetime.now(datetime.UTC)
        stmt = (
            update(Approval)
            .where(Approval.status == "pending")
            .where(Approval.expires_at < now)
            .values(status="expired")
        )
        result = conn.execute(stmt)
        conn.commit()
        
        logger.info(f"Expired {result.rowcount} approvals.")

if __name__ == "__main__":
    expire_approvals()
