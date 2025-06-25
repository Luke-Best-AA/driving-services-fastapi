from app.main import app
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    import uvicorn
    env = os.getenv("ENV", "dev")
    host = os.getenv("HOST", "0.0.0.0" if env == "prod" else "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    reload = env != "prod"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload, proxy_headers=True)