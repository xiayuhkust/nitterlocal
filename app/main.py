from fastapi import FastAPI, Form, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
import subprocess
import urllib.parse

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
        # Import the database_sync module
        from app.database_sync import get_sqlite_kol_character_stats, get_sqlite_url_tracking_stats
        
        # Just synchronize without processing a file
        results = {
            "excel_processing": None,
            "mysql_sync": None,
            "sqlite_kol_character_stats": get_sqlite_kol_character_stats('/home/ubuntu/nitterlocal/data/local_database.db'),
            "sqlite_url_tracking_stats": get_sqlite_url_tracking_stats('/home/ubuntu/nitterlocal/data/local_database.db')
        }
        
        # Run the combined synchronization script
        try:
            script_path = '/home/ubuntu/nitterlocal/scripts/sync/sync_to_mysql_combined.py'
            
            # Check if the script exists
            if not os.path.exists(script_path):
                logging.error(f"Script not found: {script_path}")
                results["mysql_sync"] = {"success": False, "processed_count": 0, "output": "", "errors": f"Script not found: {script_path}"}
            else:
                # Make sure the script is executable
                os.chmod(script_path, 0o755)
                
                # Run the script
                cmd = [
                    'python3',
                    script_path
                ]
                
                if test_mode:
                    cmd.append('--test')
                
                logging.info(f"Running command: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                results["mysql_sync"] = {
                    "success": True,
                    "processed_count": 0,  # Add processed_count for UI compatibility
                    "output": result.stdout,
                    "errors": result.stderr
                }
        except Exception as e:
            logging.error(f"Error syncing to MySQL: {str(e)}")
            results["mysql_sync"] = {"success": False, "processed_count": 0, "output": "", "errors": str(e)}
        
        return results
    
    except Exception as e:
        logging.error(f"Error synchronizing database: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error synchronizing database: {str(e)}")

@app.post("/api/sync-database")
async def sync_database(
    background_tasks: BackgroundTasks,
    file_id: str = Form(default="", description="ID of the uploaded file"),
    sync_to_mysql: bool = Form(default=True, description="Whether to synchronize with MySQL"),
    test_mode: bool = Form(default=False, description="Whether to run in test mode")
):
    """Synchronize database tables after processing an Excel file"""
    try:
        # Import the database_sync module
        from app.database_sync import get_sqlite_kol_character_stats, get_sqlite_url_tracking_stats, process_excel_and_sync
        
        # If file_id is provided, process the Excel file
        if file_id:
            # Decode the URL-encoded filename
            import urllib.parse
            file_id = urllib.parse.unquote(file_id)
            
            # Check if the file exists
            file_path = os.path.join('/home/ubuntu/nitterlocal/uploads', file_id)
            logging.info(f"Looking for file at path: {file_path}")
            
            if not os.path.exists(file_path):
                # Try to find the file by partial match if exact match fails
                dir_files = os.listdir('/home/ubuntu/nitterlocal/uploads')
                potential_matches = [f for f in dir_files if f.startswith(file_id[:30])]
                
                if potential_matches:
                    file_path = os.path.join('/home/ubuntu/nitterlocal/uploads', potential_matches[0])
                    logging.info(f"Found potential match: {file_path}")
                else:
                    # Log the error for debugging
                    logging.error(f"File not found: {file_path}")
                    from fastapi import HTTPException
                    raise HTTPException(status_code=404, detail=f"File {file_id} not found")
            
            # Process the Excel file and synchronize data
            results = process_excel_and_sync(
                excel_path=file_path,
                db_path='/home/ubuntu/nitterlocal/data/local_database.db',
                sync_to_mysql=sync_to_mysql,
                test_mode=test_mode
            )
        else:
            # Just synchronize without processing a file
            results = {
                "excel_processing": None,
                "mysql_sync": None,
                "sqlite_kol_character_stats": get_sqlite_kol_character_stats('/home/ubuntu/nitterlocal/data/local_database.db'),
                "sqlite_url_tracking_stats": get_sqlite_url_tracking_stats('/home/ubuntu/nitterlocal/data/local_database.db')
            }
            
            # Run the combined synchronization script
            try:
                script_path = '/home/ubuntu/nitterlocal/scripts/sync/sync_to_mysql_combined.py'
                
                # Check if the script exists
                if not os.path.exists(script_path):
                    logging.error(f"Script not found: {script_path}")
                    results["mysql_sync"] = {"success": False, "processed_count": 0, "output": "", "errors": f"Script not found: {script_path}"}
                else:
                    # Make sure the script is executable
                    os.chmod(script_path, 0o755)
                    
                    # Run the script
                    cmd = [
                        'python3',
                        script_path
                    ]
                    
                    if test_mode:
                        cmd.append('--test')
                    
                    logging.info(f"Running command: {' '.join(cmd)}")
                    
                    result = subprocess.run(
                        cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    results["mysql_sync"] = {
                        "success": True,
                        "processed_count": 0,  # Add processed_count for UI compatibility
                        "output": result.stdout,
                        "errors": result.stderr
                    }
            except Exception as e:
                logging.error(f"Error syncing to MySQL: {str(e)}")
                results["mysql_sync"] = {"success": False, "processed_count": 0, "output": "", "errors": str(e)}
        
        return results
    
    except Exception as e:
        logging.error(f"Error synchronizing database: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Error synchronizing database: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Twitter URL ID Service")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=True)
