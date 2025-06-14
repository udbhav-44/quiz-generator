from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from bson import ObjectId, json_util
import json
from controllers.quiz_controller import LectureController, QuizController
from models.models import LectureModel, QuizModel
from typing import Dict, Any

router = APIRouter()

# Helper function to convert MongoDB objects to JSON
def parse_json(data):
    return json.loads(json_util.dumps(data))

class LectureRequest(BaseModel):
    courseCode: str
    year: int
    quarter: str
    videoId: str
    videoUrl: str
    transcriptUrl: str

@router.post("/api/lectures")
async def create_lecture(lecture: LectureRequest):
    """
    Create a new lecture entry with video and transcript URLs
    Returns the ID of the created document
    """
    try:
        lecture_id = await LectureController.create_lecture(lecture.dict())
        return JSONResponse(content={"id": lecture_id}, status_code=201)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/lectures/{lecture_id}")
async def get_lecture(lecture_id: str):
    """
    Get lecture information by ID
    """
    try:
        lecture = await LectureController.get_lecture(lecture_id)
        return JSONResponse(content=parse_json(lecture))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/lectures/{lecture_id}/process")
async def process_lecture(lecture_id: str, background_tasks: BackgroundTasks):
    """
    Process a lecture to generate quiz
    This runs in the background as it may take some time
    """
    try:
        # Check if lecture is already completed
        lecture = await LectureController.get_lecture(lecture_id)
        if lecture.get("status") == "completed":
            return JSONResponse(
                content={"message": f"Lecture {lecture_id} has already been processed and completed"},
                status_code=200
            )
        
        # If not completed, start the processing
        background_tasks.add_task(LectureController.process_lecture, lecture_id)
        return JSONResponse(content={"message": f"Processing started for lecture {lecture_id}"})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/lectures/{lecture_id}/status")
async def get_lecture_status(lecture_id: str):
    """
    Get the processing status of a lecture
    """
    try:
        lecture = await LectureController.get_lecture(lecture_id)
        return JSONResponse(content={"status": lecture["status"]})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/lectures/{lecture_id}/quiz")
async def get_lecture_quiz(lecture_id: str):
    """
    Get quiz associated with a lecture
    """
    try:
        quiz = await QuizController.get_quiz_by_lecture(lecture_id)
        return JSONResponse(content=parse_json(quiz))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/lectures/{lecture_id}/quiz/url")
async def get_lecture_quiz_content(lecture_id: str):
    """
    Get the raw quiz content associated with a lecture
    For PDF format, this will return the file URL instead of content
    """
    try:
        quiz = await QuizController.get_quiz_by_lecture(lecture_id)
        if quiz["format"] == "json":
            return JSONResponse(content={"fileUrl": quiz["fileUrl"], "format": "json"})
        else:
            # Backward compatibility for markdown content
            return Response(content=quiz["content"], media_type="text/markdown")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))     