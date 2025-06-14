import os
import numpy as np
from typing import Dict, Any
from dotenv import load_dotenv
import litellm
import time
from models import Quiz
import json
load_dotenv()
import sys
litellm.enable_json_schema_validation = False
litellm.api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL")

if not litellm.api_key or not MODEL_NAME:
    print("Missing OPENAI_API_KEY or OPENAI_MODEL in environment.")
    sys.exit(1)


# litellm.enable_json_schema_validation = True
token_usage: Dict[str, Any] = {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "steps": {}
}

def save_to_json(data, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {output_path}")
    except Exception as e:
        print(f"Error saving JSON: {e}")


def log_token_usage(step_name, input_tokens, output_tokens):
    token_usage["total_input_tokens"] += input_tokens
    token_usage["total_output_tokens"] += output_tokens
    token_usage["steps"][step_name] = {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens
    }
    print(f"Token usage for {step_name}: {input_tokens} in, {output_tokens} out")


def load_and_clean_transcript(file_path):
    print(f"Loading and cleaning transcript from {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        cleaned = [line.strip() for line in lines if '-->' not in line and not line.strip().isdigit() and line.strip() != '']
        result = "\n".join(cleaned)
        print(f"Transcript cleaned successfully. Length: {len(result)} characters")
        return result
    except Exception as e:
        print(f"Error while cleaning transcript: {e}")
        raise

def call_llm_with_retry(messages, max_retries=5, base_delay=1, max_delay=60):
    """Call LiteLLM with exponential backoff retry mechanism for rate limits"""
    for attempt in range(max_retries):
        try:
            response = litellm.completion(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                response_format=Quiz
            )
            return response
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "Too Many Requests" in error_str or "rate limit" in error_str.lower():
                if attempt < max_retries - 1:
                    # Extract retry-after if available
                    retry_after = 1
                    if "retry-after" in error_str:
                        try:
                            # Try to extract retry-after value from error
                            import re
                            match = re.search(r"retry-after['\"]?\s*:\s*['\"]?(\d+)", error_str)
                            if match:
                                retry_after = int(match.group(1))
                        except:
                            pass
                    
                    # Use exponential backoff with jitter, but respect retry-after
                    delay = min(max(base_delay * (2 ** attempt), retry_after), max_delay)
                    jitter = delay * 0.1 * np.random.random()  # Add 10% jitter
                    total_delay = delay + jitter
                    
                    print(f"Rate limit hit (attempt {attempt + 1}/{max_retries}). Retrying in {total_delay:.2f} seconds...")
                    time.sleep(total_delay)
                    continue
                else:
                    print(f"Rate limit exceeded after {max_retries} attempts")
                    raise
            else:
                # For non-rate-limit errors, raise immediately
                print(f"LLM API error: {error_str}")
                raise
    
    raise Exception(f"Failed to complete request after {max_retries} retries")



def timestamp_to_seconds(timestamp):
    h, m, s = map(int, timestamp.split(":"))
    return h * 3600 + m * 60 + s




def generate_questions(transcript):
    print("Generating questions from transcript")
    try:
        prompt = """
        Using the provided transcript, generate a deep understanding based structured quiz that evaluates comprehension across different Bloom's Taxonomy Levels. Focus on identifying key learning objectives, factual knowledge,solving based questions and conceptual understanding.
        The quiz should be structured as a list of 10 questions, each with 4 options, a correct option, an explanation, and a time stamp.
        Example:
                {
        "questions": [
            {
            "question": "...",
            "options": ["...", "...", "...", "..."],
            "correct_option": "...",
            "explanation": "...",
            "time_stamp": "00:12:34"
            },
            ...
        ]
        }

    While creating questions, frame questions that test understanding of:
        DO NOT INCLUDE ANY QUESTIONS THAT ARE NOT MENTIONED IN THE TRANSCRIPT.
        1. Accurate, subject-centered scientific questions
        1. Definitions, processes, formulas, and steps
        2. Cause-effect relationships
        3. Interpretation of visual aids if referenced
        4. Problem-solving or reasoning based on the transcript
        5. No references to "professor", "assignments", or "recorded sessions"
        
        Provide realistic options, including common misconceptions.

        Ensure explanations clarify the logic behind the correct answer.

        Add the time stamp in the format HH:MM:SS from the transcript where the answer is mentioned or implied.

        """
        
        messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": transcript}
]
        
        response = call_llm_with_retry(messages)
        
        # Use actual token usage from LiteLLM response
        usage = response.usage
        log_token_usage("Quiz Generation", usage.prompt_tokens, usage.completion_tokens)

        # outline = response
        outline_text = response.choices[0].message["content"]
        outline = json.loads(outline_text) 
        
        return outline
    except Exception as e:
        print(f"Error generating outline: {e}")
        raise




def run_pipeline(transcript_path, output_path):
    print(f"Running pipeline for transcript: {transcript_path}")
    try:
        clean_transcript = load_and_clean_transcript(transcript_path)
        questions = generate_questions(clean_transcript)
        save_to_json(questions, output_path)    

    
        print("\n=== Token Usage Summary ===")
        print(f"Total Input Tokens: {token_usage['total_input_tokens']}")
        print(f"Total Output Tokens: {token_usage['total_output_tokens']}")
        
        # Print step-by-step breakdown of token usage
        for step, usage in token_usage["steps"].items():
            print(f"  {step}: {usage['input']} in, {usage['output']} out, {usage['total']} total")
        
        # return questions
    except Exception as e:
        print(f"Error in pipeline execution: {e}")
        raise

if __name__ == "__main__":
    os.makedirs('Data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    transcript_dir = 'Data/Transcript'
 
    os.makedirs(transcript_dir, exist_ok=True)
    
    pdf_output = run_pipeline(
        transcript_path="Data/Transcript/video.txt",
    )
    output_file = "output/generated_quiz.json"
    save_to_json(pdf_output, output_file)

