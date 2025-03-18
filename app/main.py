from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os
import tempfile
import shutil
import logging
import urllib.parse
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.twitter_utils import process_twitter_urls, extract_twitter_handle, get_user_id_from_twitter_handle
from app.excel_processor import ExcelProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="Twitter URL to ID Service",
    description="API for extracting Twitter IDs from URLs in Excel files",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Create uploads directory in nitterlocal to share files between projects
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create temporary directory for processed files in nitterlocal
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# Create static directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    """Root endpoint that serves the HTML form for file uploads"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload an Excel file containing Twitter URLs
    
    The file will be saved temporarily and basic validation will be performed
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
    
    try:
        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Basic validation - try to open the file with pandas
        try:
            df = pd.read_excel(file_path)
            row_count = len(df)
            column_count = len(df.columns)
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")
        
        return {
            "filename": filename,
            "file_path": file_path,
            "size": os.path.getsize(file_path),
            "rows": row_count,
            "columns": column_count,
            "message": "File uploaded successfully"
        }
    
    except Exception as e:
        logging.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/api/process-twitter-urls")
async def process_twitter_urls_endpoint(urls: List[str]):
    """
    Process a list of Twitter URLs and extract their user IDs
    
    Args:
        urls: List of Twitter URLs to process
        
    Returns:
        List of processed URLs with their user IDs
    """
    try:
        # Process the Twitter URLs
        results = process_twitter_urls(urls)
        
        return {
            "total": len(urls),
            "successful": sum(1 for url in results if url["status"] == "success"),
            "failed": sum(1 for url in results if url["status"] == "error"),
            "results": results
        }
    
    except Exception as e:
        logging.error(f"Error processing Twitter URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing Twitter URLs: {str(e)}")

@app.post("/api/process-excel")
async def process_excel(background_tasks: BackgroundTasks, file_id: str = Form(...)):
    """
    Process an Excel file that has been uploaded and extract Twitter IDs
    
    Args:
        file_id: ID of the uploaded file (filename)
        
    Returns:
        Processing results and path to the processed file
    """
    try:
        # Check if the file exists
        file_id = urllib.parse.unquote(file_id)  # Decode the URL-encoded filename
        # Ensure the filename is properly decoded for spaces and special characters
        file_path = os.path.join(UPLOAD_DIR, file_id)
        logging.info(f"Looking for file at path: {file_path}")
        
        if not os.path.exists(file_path):
            # Try to find the file by partial match if exact match fails
            dir_files = os.listdir(UPLOAD_DIR)
            potential_matches = [f for f in dir_files if f.startswith(file_id[:30])]
            
            if potential_matches:
                file_path = os.path.join(UPLOAD_DIR, potential_matches[0])
                logging.info(f"Found potential match: {file_path}")
            else:
                # Log the error for debugging
                logging.error(f"File not found: {file_path}")
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        # Copy the file to the data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        data_file_path = os.path.join(data_dir, os.path.basename(file_path))
        shutil.copy2(file_path, data_file_path)
        logging.info(f"Copied file to data directory: {data_file_path}")
        
        # Use create_and_process_test_excel.py to process the Excel file
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'newstruct', 'create_and_process_test_excel.py')
        
        if not os.path.exists(script_path):
            logging.error(f"Script not found: {script_path}")
            raise HTTPException(status_code=500, detail=f"Script not found: {script_path}")
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Run the script with the Excel file path
        cmd = [
            'python3',
            script_path,
            '--excel', data_file_path
        ]
        
        logging.info(f"Running command: {' '.join(cmd)}")
        
        # Capture the output for processing
        import subprocess
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Initialize the Excel processor for backward compatibility
        processor = ExcelProcessor(UPLOAD_DIR, TEMP_DIR)
        
        # Process the Excel file using the existing processor for UI compatibility
        results = processor.process_excel(file_path)
        
        # Add the IDs to the Excel file for download
        processed_file_path = processor.add_ids_to_excel(file_path, results["processed_urls"])
        
        # Schedule the temporary files for deletion after 1 hour
        def cleanup_temp_files():
            try:
                # Wait for 1 hour
                import time
                time.sleep(3600)
                
                # Delete the files
                if os.path.exists(file_path):
                    os.remove(file_path)
                if os.path.exists(processed_file_path):
                    os.remove(processed_file_path)
                if os.path.exists(data_file_path):
                    os.remove(data_file_path)
                    
                logging.info(f"Cleaned up temporary files: {file_path}, {processed_file_path}, {data_file_path}")
            except Exception as e:
                logging.error(f"Error cleaning up temporary files: {str(e)}")
        
        background_tasks.add_task(cleanup_temp_files)
        
        # Return the results
        return {
            "original_file": file_id,
            "processed_file": os.path.basename(processed_file_path),
            "download_url": f"/api/download/{os.path.basename(processed_file_path)}",
            "results": results,
            "script_output": result.stdout
        }
    
    except Exception as e:
        logging.error(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    Download a processed Excel file
    
    Args:
        filename: Name of the file to download
        
    Returns:
        The file as a download
    """
    try:
        # Check if the file exists
        file_path = os.path.join(TEMP_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File {filename} not found")
        
        # Return the file
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except Exception as e:
        logging.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.post("/api/sync-database")
async def sync_database(
    background_tasks: BackgroundTasks,
    file_id: str = Form(...),
    sync_to_mysql: bool = Form(True),
    test_mode: bool = Form(False)
):
    """
    Synchronize database tables after processing an Excel file
    
    Args:
        file_id: ID of the uploaded file (filename)
        sync_to_mysql: Whether to synchronize with MySQL
        test_mode: Whether to run in test mode (no actual MySQL updates)
        
    Returns:
        Synchronization results
    """
    try:
        # Check if the file exists
        file_id = urllib.parse.unquote(file_id)  # Decode the URL-encoded filename
        # Ensure the filename is properly decoded for spaces and special characters
        file_path = os.path.join(UPLOAD_DIR, file_id)
        logging.info(f"Looking for file at path: {file_path}")
        
        if not os.path.exists(file_path):
            # Try to find the file by partial match if exact match fails
            dir_files = os.listdir(UPLOAD_DIR)
            potential_matches = [f for f in dir_files if f.startswith(file_id[:30])]
            
            if potential_matches:
                file_path = os.path.join(UPLOAD_DIR, potential_matches[0])
                logging.info(f"Found potential match: {file_path}")
            else:
                # Log the error for debugging
                logging.error(f"File not found: {file_path}")
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        
        # Import the database_sync module
        from app.database_sync import process_excel_and_sync, get_sqlite_kol_character_stats, get_sqlite_url_tracking_stats
        
        # Process the Excel file and synchronize data
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'local_database.db')
        results = process_excel_and_sync(
            excel_path=file_path,
            db_path=db_path,
            sync_to_mysql=False,  # Don't sync to MySQL immediately
            test_mode=test_mode
        )
        
        # Add a message about automatic synchronization
        results["mysql_sync_message"] = "数据将在15分钟内自动同步到MySQL数据库"
        
        return results
    
    except Exception as e:
        logging.error(f"Error synchronizing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error synchronizing database: {str(e)}")

@app.post("/api/sync-mysql")
async def sync_mysql_only(
    background_tasks: BackgroundTasks,
    sync_to_mysql: bool = Form(True),
    test_mode: bool = Form(False)
):
    """Synchronize database tables with MySQL without requiring a file"""
    try:
        # Import the database_sync module
        from app.database_sync import get_sqlite_kol_character_stats, get_sqlite_url_tracking_stats
        
        # Run the combined synchronization script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'sync', 'sync_to_mysql_combined.py')
        
        if not os.path.exists(script_path):
            logging.error(f"Script not found: {script_path}")
            raise HTTPException(status_code=404, detail=f"Script not found: {script_path}")
        
        # Make sure the script is executable
        os.chmod(script_path, 0o755)
        
        # Run the script
        cmd = ['python3', script_path]
        if test_mode:
            cmd.append('--test')
        
        import subprocess
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        return {
            "sqlite_kol_character_stats": get_sqlite_kol_character_stats(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'local_database.db')),
            "sqlite_url_tracking_stats": get_sqlite_url_tracking_stats(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'local_database.db')),
            "mysql_sync": {"success": True, "processed_count": 0, "output": result.stdout, "errors": result.stderr}
        }
    
    except Exception as e:
        logging.error(f"Error synchronizing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error synchronizing database: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Twitter URL ID Service")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()
    
    # Run the server with the specified host and port
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=True)
