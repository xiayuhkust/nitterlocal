from fastapi import FastAPI, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create the FastAPI app
app = FastAPI(title="Twitter URL ID Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Create Jinja2 templates
templates = Jinja2Templates(directory=STATIC_DIR)

@app.get("/")
async def read_root(request: Request):
    """Serve the index.html file"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/sync-mysql")
async def sync_mysql_only(
    background_tasks: BackgroundTasks,
    sync_to_mysql: bool = Form(default=True),
    test_mode: bool = Form(default=False)
):
    """Synchronize database tables with MySQL without requiring a file"""
    try:
        script_path = '/home/ubuntu/nitterlocal/scripts/sync/sync_to_mysql_combined.py'
        if not os.path.exists(script_path):
            return {"success": False, "error": f"Script not found: {script_path}"}
        
        os.chmod(script_path, 0o755)
        cmd = ['python3', script_path]
        if test_mode:
            cmd.append('--test')
        
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return {"success": True, "output": result.stdout, "errors": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/sync-database")
async def sync_database(
    background_tasks: BackgroundTasks,
    file_id: str = Form(default=""),
    sync_to_mysql: bool = Form(default=True),
    test_mode: bool = Form(default=False)
):
    """Synchronize database tables after processing an Excel file"""
    try:
        script_path = '/home/ubuntu/nitterlocal/scripts/sync/sync_to_mysql_combined.py'
        if not os.path.exists(script_path):
            return {"success": False, "error": f"Script not found: {script_path}"}
        
        os.chmod(script_path, 0o755)
        cmd = ['python3', script_path]
        if test_mode:
            cmd.append('--test')
        
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return {"success": True, "output": result.stdout, "errors": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Twitter URL ID Service")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=True)
