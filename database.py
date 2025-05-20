import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs
from bson import ObjectId

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

    def store_pdf(self, pdf_path, url, user_id, metadata=None):
        """
        Store PDF in MongoDB using GridFS
        Args:
            pdf_path: Path to the PDF file
            url: URL or description of the report
            user_id: ID of the user who created the report
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
                'type': metadata.get('type', 'accessibility_report') if metadata else 'accessibility_report',
                'user_id': user_id
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

    def get_pdf(self, file_id, user_id=None):
        """
        Retrieve PDF from MongoDB
        Args:
            file_id: ID of the PDF file
            user_id: Optional user ID to verify ownership
        Returns: The PDF data and filename
        """
        try:
            file_data = self.fs.get(ObjectId(file_id))
            
            # Check if user has access to this file
            if user_id and file_data.metadata.get('user_id') != user_id:
                raise Exception("Access denied")
                
            return file_data.read(), file_data.filename
        except Exception as e:
            raise Exception(f"Failed to retrieve PDF: {str(e)}")

    def list_reports(self, user_id):
        """
        List all accessibility reports for a specific user
        Args:
            user_id: ID of the user
        Returns: List of report metadata
        """
        reports = []
        for grid_out in self.fs.find({
            "metadata.type": "accessibility_report",
            "metadata.user_id": user_id
        }):
            reports.append({
                'file_id': str(grid_out._id),
                'filename': grid_out.filename,
                'url': grid_out.metadata.get('url'),
                'timestamp': grid_out.metadata.get('timestamp'),
                'type': grid_out.metadata.get('type')
            })
        return reports 