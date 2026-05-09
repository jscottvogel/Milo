import os
import shutil
import uuid
import tempfile

# Ensure cross platform compatibility while respecting the /tmp requirement conceptually
TEMP_DIR = os.path.abspath("/tmp/milo_parse")

class TempFileManager:
    @classmethod
    def setup(cls):
        """Clean and recreate the temp directory on process startup."""
        try:
            if os.path.exists(TEMP_DIR):
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
            os.makedirs(TEMP_DIR, exist_ok=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not setup temp dir {TEMP_DIR}: {e}")
        
    @classmethod
    def get_temp_path(cls, filename: str) -> str:
        """Generate a UUID-isolated temp path for a file."""
        try:
            if not os.path.exists(TEMP_DIR):
                os.makedirs(TEMP_DIR, exist_ok=True)
        except Exception:
            pass # fallback to trying to write anyway
            
        unique_id = str(uuid.uuid4())
        safe_filename = os.path.basename(filename)
        return os.path.join(TEMP_DIR, f"{unique_id}_{safe_filename}")
