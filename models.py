from pydantic import BaseModel, Field


class Question(BaseModel):
    question: str = Field(description="Clear, concise question based on the transcript")
    options: list[str] = Field(description="4 plausible multiple-choice options")
    correct_option: str = Field(description="The correct answer from the options list")
    explanation: str = Field(description="Brief rationale or clarification for the correct answer")
    bloom_level: str = Field(description="Bloom's Taxonomy Level")
    time_stamp: str = Field(description="Time in the transcript where the answer is discussed")

class Quiz(BaseModel):
    questions: list[Question] = Field(description="Complete quiz as a list of such questions")
    
    
    