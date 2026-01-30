import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7001))
    uvicorn.run("main:app", port=port, reload=True, ws_max_size=1024 * 1024 * 100)
