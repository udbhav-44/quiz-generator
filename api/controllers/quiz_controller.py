import os
import sys
import tempfile
import requests
import logging
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException
from config.database import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import from original codebase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from script import run_pipeline



logger = logging.getLogger(__name__)

class LectureController:
    
    @staticmethod
    async def check_duplicate_lecture(lecture_data):
        """
        Check if a lecture with the same details already exists
        Returns the existing lecture if found, None otherwise
        """
        try:
            collection = Database.db.lectures
            
            # Query for lectures with matching core details (excluding timestamps and status)
            query = {
                "courseCode": lecture_data["courseCode"],
                "year": lecture_data["year"],
                "quarter": lecture_data["quarter"],
                "videoId": lecture_data["videoId"],
                "videoUrl": lecture_data["videoUrl"],
                "transcriptUrl": lecture_data["transcriptUrl"]
            }
            
            existing_lecture = await collection.find_one(query)
            return existing_lecture
        except Exception as e:
            logger.error(f"Error checking for duplicate lecture: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to check for duplicate lecture: {str(e)}")
    
    
    @staticmethod
    async def create_lecture(lecture_data):
        """
        Create a new lecture entry in the database
        Returns the ID of the created document
        """
        try:
            # Check for duplicate lecture first
            existing_lecture = await LectureController.check_duplicate_lecture(lecture_data)
            if existing_lecture:
                raise HTTPException(
                    status_code=409, 
                    detail="A lecture with these details already exists"
                )
            
            collection = Database.db.lectures
            # Set timestamps
            lecture_data["createdAt"] = datetime.utcnow()
            lecture_data["updatedAt"] = datetime.utcnow()
            lecture_data["status"] = "not started"
            
            result = await collection.insert_one(lecture_data)
            return str(result.inserted_id)
        except HTTPException as e:
            # Re-raise HTTPException (including duplicate check error)
            raise e
        except Exception as e:
            logger.error(f"Error creating lecture: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create lecture: {str(e)}")
        
    @staticmethod
    async def get_lecture(lecture_id):
        """Get a lecture by ID"""
        try:
            collection = Database.db.lectures
            lecture = await collection.find_one({"_id": ObjectId(lecture_id)})
            if not lecture:
                raise HTTPException(status_code=404, detail=f"Lecture with ID {lecture_id} not found")
            return lecture
        except Exception as e:
            logger.error(f"Error retrieving lecture: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve lecture: {str(e)}")

    @staticmethod
    async def process_lecture(lecture_id):
        """
        Process a lecture to generate quiz
        1. Download transcript
        2. Run pipeline to generate quiz
        3. Save quiz to database
        4. Update lecture status
        """
        try:
            # Get lecture data
            collection = Database.db.lectures
            lecture = await collection.find_one({"_id": ObjectId(lecture_id)})
            if not lecture:
                raise HTTPException(status_code=404, detail=f"Lecture with ID {lecture_id} not found")
            
            # Update lecture status to processing
            await collection.update_one(
                {"_id": ObjectId(lecture_id)},
                {"$set": {"status": "processing", "updatedAt": datetime.utcnow()}}
            )
            
            # Import utility function
            from utils.quiz_utils import download_file
            
            try:
                # Download transcript
                transcript_path = await download_file(lecture['transcriptUrl'], ".txt")
            except HTTPException as e:
                await collection.update_one(
                    {"_id": ObjectId(lecture_id)},
                    {"$set": {"status": "failed", "updatedAt": datetime.utcnow(), "error": str(e.detail)}}
                )
                raise
            
            # Set up output path for markdown
            temp_output_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
            json_output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'json')
            os.makedirs(json_output_dir, exist_ok=True)
            # Run pipeline to generate quiz
            logger.info(f"Running pipeline for lecture {lecture_id}")
            os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
            os.environ["OPENAI_MODEL"] = os.getenv("OPENAI_MODEL", "gpt-4o")
            run_pipeline(transcript_path, temp_output_json)
            
            json_file = f"lecture_{lecture_id}_quiz.json"
            permanent_json_path = os.path.join(json_output_dir, json_file)
            
            import shutil
            # Move temporary JSON file to permanent directory
            shutil.move(temp_output_json, permanent_json_path)
            
            json_file_url = f"/api/output/json/{json_file}"
            
            # Save quiz to database
            quiz_collection = Database.db.quiz
            quiz_data = {
                "lectureId": ObjectId(lecture_id),
                "fileUrl": json_file_url,
                "format": "json",
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            quiz_result = await quiz_collection.insert_one(quiz_data)
            
            # Update lecture status to completed
            await collection.update_one(
                {"_id": ObjectId(lecture_id)},
                {"$set": {
                    "status": "completed", 
                    "updatedAt": datetime.utcnow(),
                    "quizId": quiz_result.inserted_id
                }}
            )
            
            # Clean up temporary files
            os.remove(transcript_path)
            os.remove(temp_output_json)
            
            return {
                "lectureId": str(lecture_id),
                "quizId": str(quiz_result.inserted_id),
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Error processing lecture: {e}")
            # Update lecture status to failed
            try:
                await collection.update_one(
                    {"_id": ObjectId(lecture_id)},
                    {"$set": {"status": "failed", "updatedAt": datetime.utcnow(), "error": str(e)}}
                )
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to process lecture: {str(e)}")

class QuizController:
    
    @staticmethod
    async def get_quiz_by_lecture(lecture_id):
        """Get quiz by lecture ID"""
        try:
            collection = Database.db.quiz
            quiz = await collection.find_one({"lectureId": ObjectId(lecture_id)})
            if not quiz:
                raise HTTPException(status_code=404, detail=f"Quiz for lecture {lecture_id} not found")
            return quiz
        except Exception as e:
            logger.error(f"Error retrieving quiz by lecture: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve quiz: {str(e)}")