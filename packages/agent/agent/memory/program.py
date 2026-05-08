import os
import boto3
from db.models.identity import Milo
from db.models.program import WorkItem
from sqlalchemy.orm import Session


class ProgramMemory:
    """
    Structured fetcher from the programs, milestones, tasks, risks, decisions, commitments tables.
    """
    def __init__(self, session: Session):
        self.session = session

    def get_context(self, milo_id: str | None = None) -> str:
        if not milo_id:
            return "No specific program selected."

        milo = self.session.get(Milo, milo_id)
        if not milo or not milo.default_work_item_id:
            return "No specific program selected."

        program = self.session.query(WorkItem).filter(WorkItem.id == milo.default_work_item_id).first()
        if not program:
            return "Program not found."

        context_str = f"Program Name: {program.name}\nDescription: {program.description}\nStatus: {program.status}\n\n"
        
        # Inject Artifact list
        bucket = os.environ.get("S3_BUCKET_NAME", "milo-artifacts-poc")
        prefix = f"{program.tenant_id}/work_items/{program.id}/"
        try:
            s3 = boto3.client('s3')
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                context_str += "### Available Program Artifacts in Storage ###\n"
                context_str += "You can read these files using the storage.read tool with the exact paths listed below:\n\n"
                for obj in response['Contents']:
                    if not obj['Key'].endswith('/'):
                        # Provide the path relative to the tenant, which is what storage.read expects
                        relative_path = obj['Key'].replace(f"{program.tenant_id}/", "")
                        context_str += f"- {relative_path}\n"
            else:
                context_str += "No artifacts currently uploaded to this program.\n"
        except Exception as e:
            context_str += f"Note: Unable to fetch artifacts from S3 ({str(e)}).\n"

        return context_str
