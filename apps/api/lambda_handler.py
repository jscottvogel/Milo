from mangum import Mangum
from app.main import app

# Specify text/event-stream so mangum doesn't base64 encode it
handler = Mangum(app, text_mime_types=[
    "text/event-stream",
    "text/plain",
    "text/html",
    "application/json"
])
