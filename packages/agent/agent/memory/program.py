from db.models import Program
from sqlalchemy.orm import Session


class ProgramMemory:
    """
    Structured fetcher from the programs, milestones, tasks, risks, decisions, commitments tables.
    """
    def __init__(self, session: Session):
        self.session = session

    def get_context(self, program_id: str = None) -> str:
        # In a real implementation this would join across the tables.
        # For Phase 3, we just fetch a basic string or the summary.
        if not program_id:
            return "No specific program selected."

        program = self.session.query(Program).filter(Program.id == program_id).first()
        if not program:
            return "Program not found."

        return f"Program Name: {program.name}\nDescription: {program.description}\nStatus: {program.status}"
