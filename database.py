import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Get MongoDB URI from environment variables
        self.mongo_uri = os.getenv('MONGO_URI')
        if not self.mongo_uri:
            raise ValueError("MongoDB URI not found in environment variables")
        
        # Initialize MongoDB client
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['accessibility_reports']
        self.fs = gridfs.GridFS(self.db)

    def store_pdf(self, pdf_path, url, metadata=None):
        """
        Store PDF in MongoDB using GridFS
        Args:
            pdf_path: Path to the PDF file
            url: URL or description of the report
            metadata: Additional metadata to store (optional)
        Returns: The ID of the stored file
        """
        try:
            # Read the PDF file
            with open(pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
            
            # Prepare metadata
            base_metadata = {
                'url': url,
                'timestamp': datetime.now(),
                'type': metadata.get('type', 'accessibility_report') if metadata else 'accessibility_report'
            }
            
            # Add additional metadata if provided
            if metadata:
                base_metadata.update(metadata)
            
            # Store in GridFS
            file_id = self.fs.put(
                pdf_data,
                filename=f'accessibility-report-{datetime.now().strftime("%Y%m%d-%H%M%S")}.pdf',
                metadata=base_metadata
            )
            
            return str(file_id)
        
        except Exception as e:
            raise Exception(f"Failed to store PDF: {str(e)}")

    def get_pdf(self, file_id):
        """
        Retrieve PDF from MongoDB
        Returns: The PDF data and filename
        """
        try:
            file_data = self.fs.get(file_id)
            return file_data.read(), file_data.filename
        except Exception as e:
            raise Exception(f"Failed to retrieve PDF: {str(e)}")

    def list_reports(self):
        """
        List all accessibility reports
        Returns: List of report metadata
        """
        reports = []
        for grid_out in self.fs.find({"metadata.type": "accessibility_report"}):
            reports.append({
                'file_id': str(grid_out._id),
                'filename': grid_out.filename,
                'url': grid_out.metadata.get('url'),
                'timestamp': grid_out.metadata.get('timestamp')
            })
        return reports 