from logger import log
from postgres_db.orm import DataAccess
from generator import mcp
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

def main():
    log.info("Starting database initialization...")
    try:
        DataAccess.create_table()
        log.info("Database tables verified/created successfully.")
    except Exception as e:
        log.error("Database initialization failed", error=str(e))
        return

    log.info("Launching MCP server via FastMCP...")

    mcp_app = mcp.sse_app()
    mcp_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(
        mcp_app,
        host="0.0.0.0",
        port=8000,
        access_log=True,
        timeout_keep_alive=65,
        headers=[
            ("Cache-Control", "no-cache"),
            ("Connection", "keep-alive"),
            ("X-Accel-Buffering", "no")
        ]
        )

if __name__ == "__main__":
    main()