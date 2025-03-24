from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
import json
import csv
import time
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi  # Add this import
import ollama

# Path to the CSV file
CSV_FILE = "./analyzed_comments_ollama_sentiment.csv"
def format_duration(duration):
    if duration == 'N/A':
        return 'N/A'
    # Convert nanoseconds to seconds and format with 2 decimal places
    return f"{duration / 1e9:.2f}"

def save_to_csv(comment, sentiment, reasoning=None, model=None, transcript_provided=False, video_id=None, ollama_response = None, seed = None, num_ctx = None):
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow([
                "Timestamp", "Comment", "Sentiment", "Reasoning", 
                "Model", "Total_Duration", "Load_Duration", "Prompt_Eval_Count",
                "Prompt_Eval_Duration", "Eval_Count", "Eval_Duration",
                "TranscriptProvided", "VideoID", "seed", "num_ctx"
            ])
     

        # Format Ollama timing metrics if available
        total_duration = format_duration(ollama_response.get('total_duration') if ollama_response else 'N/A')
        load_duration = format_duration(ollama_response.get('load_duration') if ollama_response else 'N/A')
        prompt_eval_duration = format_duration(ollama_response.get('prompt_eval_duration') if ollama_response else 'N/A')
        eval_duration = format_duration(ollama_response.get('eval_duration') if ollama_response else 'N/A')
        
        # Write the comment data with execution time
        writer.writerow([
            datetime.now().isoformat(),
            comment,
            sentiment,
            reasoning,
            model,
            total_duration,
            load_duration,
            ollama_response.get('prompt_eval_count') if ollama_response else 'N/A',
            prompt_eval_duration,
            ollama_response.get('eval_count') if ollama_response else 'N/A',
            eval_duration,
            "Yes" if transcript_provided else "No",
            video_id,
            seed,
            num_ctx
        ])


# Create a FastAPI instance
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow CORS for your Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for testing)
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"


def parse_response_to_json(response):
    parsed_response = response.json()
    json_response_string = parsed_response['response']
    json_response = json.loads(json_response_string)
    return json_response


default_schema = {
    "type": "object",
    "properties": {
        "sentiment": {"enum": ["POSITIVE", "NEUTRAL", "NEGATIVE"]},
        "reasoning": {"type": "string"}
    },
    "required": ["sentiment", "reasoning"]
}


# Fix the order of operations in the analyze_comment function
@app.post("/analyze")
async def analyze_comment(request: Request):
    start_time = time.time()
    try:
        body = await request.json()
        logger.info(f"Incoming request body: {body}")
        
        comment_base = body.get("comment")
        print("comment_base: ", comment_base)
        # Removed json.dumps() to preserve emojis
        comment = comment_base
        
        model_type = body.get("modelType", "llama")
        set_model = "mistral-small:22b" #qwen2.5:0.5b
        transcript_base = body.get("transcript", "")
        transcript = transcript_base
        
        # json dumps creates a string with double quotes representing a length of 2
        if (len(transcript)>2):
            print("transcript provided", len(transcript))
            transcript_provided = True
        else:
            print("transcript not provided", len(transcript))
            transcript_provided = False

        video_id = None

        if "video_id" in body:
            video_id = body["video_id"]
        
        if not comment:
            logger.error("Comment is required")
            raise HTTPException(status_code=400, detail="Comment is required")

        if model_type == "llama":
            # Modify the prompt to include transcript context if available
            context = f"\nVideo Transcript Context:\n{transcript}" if transcript else ""
            
            prompt = f"""
            Task: Analyze the sentiment of the YouTube comment and provide detailed reasoning.
            {context}

            Instructions:
            1. Analyze the comment's emotional tone, word choice, and context
            2. If transcript is provided, consider the video context in your analysis
            3. Classify the sentiment as POSITIVE, NEUTRAL, or NEGATIVE
            4. Provide clear reasoning that includes:
               - Tone analysis
               - Key phrases or words that influenced your decision
               - Context consideration from the transcript if available
            5. Format your response as a JSON object with two fields:
               - sentiment: Your classification (POSITIVE/NEUTRAL/NEGATIVE)
               - reasoning: Your detailed analysis

            YouTube Comment to analyze:
            "{comment}"
            """
              

            schema = default_schema
            # Prepare and send the request
            
            # for reproducibility
            seed = 1
            # context length
            num_ctx = 8192 #4096 #8192 # 4096
            temperature= 0

            payload = {
                "model": "mistral-small:22b",  # Replace with the model you want to use
                "prompt": prompt,
                "stream": False,
                "format": {
                "type": "object",
                "properties": {
                    "sentiment": {"enum": ["POSITIVE", "NEUTRAL", "NEGATIVE"]},
                    "reasoning": {"type": "string"}
                },
                "required": ["sentiment", "reasoning"]
            },
                "options" :
                        {
                            "temperature": 0,
                            "seed": 1,
                            "num_ctx": 8192,
                        },
            }



            try:
                response = None
                print(payload)
                response = requests.post(OLLAMA_URL, json=payload, headers={"Content-Type": "application/json"})
                response.raise_for_status()  # This will raise an exception for bad status codes

                response_json = response.json()
                result = json.loads(response_json['response'])
                print(result)

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                raise HTTPException(status_code=503, detail="Ollama service unavailable")
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Invalid response format from Ollama: {e}")
                raise HTTPException(status_code=500, detail="Invalid response from Ollama service")
            
            try:
                sentiment = result['sentiment']
                reasoning = result['reasoning']
                logger.info(f"Sentiment analysis result: {sentiment}, Reasoning: {reasoning}")
                
                # Save the comment and analysis result to a CSV file
                execution_time = time.time() - start_time
                save_to_csv(
                    comment=comment,
                    sentiment=sentiment,
                    reasoning=reasoning,
                    model=set_model,
                    transcript_provided=transcript_provided,
                    video_id=video_id,
                    ollama_response=response_json,
                    seed=seed,
                    num_ctx=num_ctx
                )
                print("time took: ", execution_time)
                
                return {"sentiment": sentiment, "reasoning": reasoning}
                
            except KeyError as e:
                logger.error(f"Missing required fields in result: {e}")
                raise HTTPException(status_code=500, detail="Invalid response format from model")

        else:
            logger.error(f"Invalid model type: {model_type}")
            raise HTTPException(status_code=400, detail="Invalid model type")

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error analyzing comment: {str(e)}. Execution time: {execution_time:.2f}s")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_transcript")
async def get_transcript(request: Request):
    try:
        body = await request.json()
        video_id = body.get("video_id")
        
        if not video_id:
            raise HTTPException(status_code=400, detail="Video ID is required")
            
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Join all transcript text with newlines
            full_transcript = "\n".join([entry['text'] for entry in transcript])
            with open('transcript.txt', 'w') as file:
                for i in transcript:
                    file.write(i['text'] + '\n')

            return {"transcript": full_transcript}
        except Exception as e:
            logger.error(f"Failed to get transcript: {e}")
            raise HTTPException(status_code=404, detail="Could not retrieve transcript")
            
    except Exception as e:
        logger.error(f"Error processing transcript request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    model_to_load = "mistral-small:22b"


    # Load the model before starting the server


    print("Loading the model ..", model_to_load)
    response = None
    response = ollama.generate(
        model= model_to_load,
        keep_alive = -1,
        options={
                "temperature": 0,
                "seed": 1,
                "num_ctx": 8192,
                },
    )

    print(response)
    
    if (response.get('done', False)):
        print("successfull loaded: ", model_to_load)
    else:
        print("failed request")


    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
  
    # Unload the model after the server is stopped
    print("Unloading the model ..") 
    response = ollama.generate(
        model= model_to_load,
        keep_alive = 0
    )
    if (response.get('done', False)):
        print("successfull unloaded: ", model_to_load)
    else:
        print("failed request")