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

# Make sure the GEMINI_API_KEY is correctly set in the environment
from langchain_openai import ChatOpenAI


logger = logging.getLogger(__name__)

class LectureController:
    @staticmethod
    async def create_lecture(lecture_data):
        """
        Create a new lecture entry in the database
        Returns the ID of the created document
        """
        try:
            collection = Database.db.lectures
            # Set timestamps
            lecture_data["createdAt"] = datetime.utcnow()
            lecture_data["updatedAt"] = datetime.utcnow()
            lecture_data["status"] = "pending"
            
            result = await collection.insert_one(lecture_data)
            return str(result.inserted_id)
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
        1. Download video and transcript
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
            from utils.file_utils import download_file
            
            try:
                # Download video and transcript
                video_path = await download_file(lecture['videoUrl'], ".mp4")
                transcript_path = await download_file(lecture['transcriptUrl'], ".txt")
            except HTTPException as e:
                await collection.update_one(
                    {"_id": ObjectId(lecture_id)},
                    {"$set": {"status": "failed", "updatedAt": datetime.utcnow(), "error": str(e.detail)}}
                )
                raise
            
            # Set up output path for markdown
            temp_output_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
            
            # Run pipeline to generate quiz
            logger.info(f"Running pipeline for lecture {lecture_id}")
            # Make sure to set the GEMINI_API_KEY environment variable
            # os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
            # os.environ["GEMINI_MODEL"] = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            run_pipeline(transcript_path, video_path, temp_output_md)
            
            # Read generated markdown file
            with open(temp_output_md, 'r', encoding='utf-8') as f:
                quiz_content = f.read()
            
            # Save quiz to database
            quiz_collection = Database.db.quiz
            quiz_data = {
                "lectureId": ObjectId(lecture_id),
                "content": quiz_content,
                "format": "md",
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
            os.remove(video_path)
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
    async def get_quiz(quiz_id):
        """Get quiz by ID"""
        try:
            collection = Database.db.quiz
            quiz = await collection.find_one({"_id": ObjectId(quiz_id)})
            if not quiz:
                raise HTTPException(status_code=404, detail=f"quiz with ID {quiz_id} not found")
            return quiz
        except Exception as e:
            logger.error(f"Error retrieving quiz: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve quiz: {str(e)}")
    
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