# Quiz Generator

An intelligent quiz generation system that automatically creates comprehensive multiple-choice questions from video transcripts using Large Language Models (LLMs). The system generates questions based on Bloom's Taxonomy levels and provides detailed explanations with timestamps.

##  Features

- **AI-Powered Question Generation**: Uses OpenAI's GPT models via LiteLLM to generate contextually relevant questions
- **Bloom's Taxonomy Integration**: Questions are categorized by cognitive levels (Understanding, Application, Analysis, etc.)
- **Timestamp References**: Each question includes a timestamp indicating where the answer is discussed in the transcript
- **Multiple Choice Format**: Generates 4 plausible options including common misconceptions
- **Detailed Explanations**: Provides rationale for correct answers to enhance learning
- **REST API**: FastAPI-based web service for easy integration
- **MongoDB Integration**: Persistent storage for generated quizzes
- **Rate Limiting & Retry Logic**: Robust error handling with exponential backoff
- **Token Usage Tracking**: Monitor API usage and costs

##  Prerequisites

- Python 3.8+
- OpenAI API key
- MongoDB (optional, for API usage)

##  Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd quiz-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory as per `.env.example`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4-turbo-preview
   PORT=8000
   MONGODB_URI=mongodb://localhost:27017/quiz_generator
   ```

##  Project Structure

```
quiz-generator/
├── api/                    # FastAPI web service
│   ├── main.py            # FastAPI application entry point
│   ├── config/            # Database and configuration
│   ├── controllers/       # Business logic
│   ├── models/           # Data models
│   ├── routes/           # API endpoints
│   └── utils/            # Utility functions
├── Data/                  # Input data directory
│   └── Transcript/       # Video transcripts
├── output/               # Generated quiz outputs
├── models.py             # Pydantic data models
├── script.py             # Main quiz generation script
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

##  Usage

### Command Line Interface

1. **Prepare your transcript**
   - Place your video transcript in `Data/Transcript/video.txt`
   - The transcript should be in plain text format

2. **Run the quiz generator**
   ```bash
   python script.py
   ```

3. **Check the output**
   - Generated quiz will be saved to `output/generated_quiz.json`

### API Usage

The Quiz Generator provides a comprehensive REST API for managing lectures and generating quizzes programmatically.

#### Starting the API Server

##### Method 1: Direct Python Execution
```bash
# Navigate to the api directory
cd api

# Start the server
python main.py
```

##### Method 2: Using Uvicorn (Recommended for Production)
```bash
# From the project root
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or with specific configuration
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

##### Method 3: Using Gunicorn (Production)
```bash
# Install gunicorn if not already installed
pip install gunicorn

# Start with gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```


2. **Access the API**
   - Base URL: `http://localhost:8000`
   - Interactive docs: `http://localhost:8000/docs` (Swagger UI)
   - Alternative docs: `http://localhost:8000/redoc` (ReDoc)

#### API Endpoints

##### 1. Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

##### 2. Create Lecture
```http
POST /api/lectures
```
**Request Body:**
```json
{
  "courseCode": "CS101",
  "year": 2024,
  "quarter": "Fall",
  "videoId": "lecture_001",
  "videoUrl": "https://example.com/video.mp4",
  "transcriptUrl": "https://example.com/transcript.txt"
}
```
**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011"
}
```

##### 3. Get Lecture Information
```http
GET /api/lectures/{lecture_id}
```
**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "courseCode": "CS101",
  "year": 2024,
  "quarter": "Fall",
  "videoId": "lecture_001",
  "videoUrl": "https://example.com/video.mp4",
  "transcriptUrl": "https://example.com/transcript.txt",
  "status": "pending",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

##### 4. Process Lecture (Generate Quiz)
```http
POST /api/lectures/{lecture_id}/process
```
**Response:**
```json
{
  "message": "Processing started for lecture 507f1f77bcf86cd799439011"
}
```

##### 5. Get Lecture Processing Status
```http
GET /api/lectures/{lecture_id}/status
```
**Response:**
```json
{
  "status": "processing"
}
```
**Possible Status Values:**
- `pending`: Lecture created, not yet processed
- `processing`: Quiz generation in progress
- `completed`: Quiz successfully generated
- `failed`: Processing failed

##### 6. Get Generated Quiz
```http
GET /api/lectures/{lecture_id}/quiz
```
**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "lectureId": "507f1f77bcf86cd799439011",
  "content": "{\"questions\":[...]}",
  "format": "json",
  "fileUrl": "https://example.com/quiz.json",
  "createdAt": "2024-01-15T10:35:00Z",
  "updatedAt": "2024-01-15T10:35:00Z"
}
```

##### 7. Get Quiz Content URL
```http
GET /api/lectures/{lecture_id}/quiz/url
```
**Response:**
```json
{
  "fileUrl": "https://example.com/quiz.json",
  "format": "json"
}
```

#### Complete API Workflow Example

Here's a complete example of using the API to generate a quiz:

```bash
# 1. Create a new lecture
curl -X POST "http://localhost:8000/api/lectures" \
  -H "Content-Type: application/json" \
  -d '{
    "courseCode": "MATH201",
    "year": 2024,
    "quarter": "Spring",
    "videoId": "linear_algebra_lecture_1",
    "videoUrl": "https://example.com/lectures/linear_algebra_1.mp4",
    "transcriptUrl": "https://example.com/transcripts/linear_algebra_1.txt"
  }'

# Response: {"id": "507f1f77bcf86cd799439011"}

# 2. Start processing the lecture
curl -X POST "http://localhost:8000/api/lectures/507f1f77bcf86cd799439011/process"

# 3. Check processing status
curl "http://localhost:8000/api/lectures/507f1f77bcf86cd799439011/status"

# 4. Once completed, retrieve the quiz
curl "http://localhost:8000/api/lectures/507f1f77bcf86cd799439011/quiz"
```

#### Python Client Example

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def create_and_process_lecture():
    # Create lecture
    lecture_data = {
        "courseCode": "CS101",
        "year": 2024,
        "quarter": "Fall",
        "videoId": "intro_to_programming",
        "videoUrl": "https://example.com/video.mp4",
        "transcriptUrl": "https://example.com/transcript.txt"
    }
    
    response = requests.post(f"{BASE_URL}/api/lectures", json=lecture_data)
    lecture_id = response.json()["id"]
    
    # Start processing
    requests.post(f"{BASE_URL}/api/lectures/{lecture_id}/process")
    
    # Poll for completion
    while True:
        status_response = requests.get(f"{BASE_URL}/api/lectures/{lecture_id}/status")
        status = status_response.json()["status"]
        
        if status == "completed":
            break
        elif status == "failed":
            raise Exception("Processing failed")
        
        time.sleep(10)  # Wait 10 seconds before checking again
    
    # Get the quiz
    quiz_response = requests.get(f"{BASE_URL}/api/lectures/{lecture_id}/quiz")
    return quiz_response.json()

# Usage
quiz = create_and_process_lecture()
print(quiz)
```

#### Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message description"
}
```

#### Rate Limiting

The API includes built-in rate limiting and retry logic for OpenAI API calls. If you encounter rate limit errors, the system will automatically retry with exponential backoff.

##  Output Format

The generated quiz follows this JSON structure:

```json
{
  "questions": [
    {
      "question": "What is the significance of the columns of matrix C?",
      "options": [
        "They can be any random set of columns from the null space.",
        "They must form a basis of the null space.",
        "They should be orthogonal to each other.",
        "They should be equal to the identity matrix."
      ],
      "correct_option": ["They must form a basis of the null space."],
      "correct_option_index": [1],
      "explanation": "The columns of matrix C must form a basis of the null space...",
      "bloom_level": "Understanding",
      "time_stamp": "00:06:45"
    }
  ]
}
```

##  Configuration

### Model Parameters

- **Temperature**: 0.1 (low randomness for consistent output)
- **Max Retries**: 5 (with exponential backoff)
- **Questions per Quiz**: 10
- **Options per Question**: 4

##  Question Generation Logic

The system generates questions that test:

1. **Factual Knowledge**: Definitions, processes, formulas
2. **Conceptual Understanding**: Cause-effect relationships
3. **Application**: Problem-solving based on transcript content
4. **Analysis**: Interpretation of concepts and relationships
5. **Bloom's Taxonomy Levels**: Questions span different cognitive levels

##  Error Handling

- **Rate Limiting**: Automatic retry with exponential backoff
- **API Failures**: Graceful error handling and logging
- **Invalid Inputs**: Validation of transcript format and content
- **Database Issues**: Connection management and fallback options

##  Token Usage Tracking

The system tracks and reports:
- Total input/output tokens
- Per-step token usage
- Cost estimation (based on OpenAI pricing)

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

##  Future Enhancements

- [ ] Support for different question types (fill-in-the-blank, short answer)
- [ ] Integration with learning management systems
- [ ] Question difficulty assessment
- [ ] Multi-language support
- [ ] Batch processing for multiple transcripts
- [ ] Question quality scoring
- [ ] Export to various formats (PDF, CSV, etc.) 