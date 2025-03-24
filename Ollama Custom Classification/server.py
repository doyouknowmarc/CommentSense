from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
import json
import csv
import time
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
import ollama

# Path to the CSV file
CSV_FILE = "./analyzed_comments_ollama_custom_classification.csv"

def format_duration(duration):
    if duration == 'N/A':
        return 'N/A'
    # Convert nanoseconds to seconds and format with 2 decimal places
    return f"{duration / 1e9:.2f}"

def save_to_csv(comment, classification, tone=None, special_flags=None, reasoning=None, model=None, 
                execution_time=None, transcript_provided=False, video_id=None, ollama_response=None, seed=None, num_ctx=None):
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow([
                "Timestamp", "Comment", "Classification", "Tone", "Special_Flags", 
                "Reasoning_Complete", "Reasoning_Sentiment", "Reasoning_Tone", "Reasoning_Special_Flags",
                "Model", "Total_Duration", "Load_Duration", "Prompt_Eval_Count",
                "Prompt_Eval_Duration", "Eval_Count", "Eval_Duration",
                "TranscriptProvided", "VideoID", "seed", "num_ctx"
            ])
        
        # Format Ollama timing metrics if available
        total_duration = format_duration(ollama_response.get('total_duration') if ollama_response else 'N/A')
        load_duration = format_duration(ollama_response.get('load_duration') if ollama_response else 'N/A')
        prompt_eval_duration = format_duration(ollama_response.get('prompt_eval_duration') if ollama_response else 'N/A')
        eval_duration = format_duration(ollama_response.get('eval_duration') if ollama_response else 'N/A')
        
        # Extract individual reasoning components
        reasoning_complete = json.dumps(reasoning) if reasoning else 'N/A'
        reasoning_sentiment = reasoning.get('sentiment', 'N/A') if reasoning else 'N/A'
        reasoning_tone = reasoning.get('tone', 'N/A') if reasoning else 'N/A'
        reasoning_special_flags = reasoning.get('special_flags', 'N/A') if reasoning else 'N/A'
        
        # Write the comment data with detailed timing metrics
        writer.writerow([
            datetime.now().isoformat(),
            comment,
            classification,
            tone,
            special_flags,
            reasoning_complete,
            reasoning_sentiment,
            reasoning_tone,
            reasoning_special_flags,
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


def create_schema():
    return {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": [
                    "Praise/Appreciation",
                    "Constructive Criticism",
                    "Video Quality Feedback",
                    "Content Correction",
                    "Personal Compliment",
                    "Creator Advice/Suggestion",
                    "Collaboration Request",
                    "Debate/Argumentation",
                    "Shared Experience",
                    "Inside Joke/Community Reference",
                    "Technical Question",
                    "Follow-Up Inquiry",
                    "Educational Addition",
                    "Nostalgia/Throwback Reaction",
                    "Cathartic Release",
                    "Outrage/Moral Judgment",
                    "Spam/Promotion",
                    "Off-Topic",
                    "Cultural Reference",
                    "Meta Commentary",
                    "Misinformation Flag"
                ]
            },
            "tone": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "Enthusiastic/Hyperbolic",
                        "Sarcastic/Ironic",
                        "Neutral/Informative",
                        "Emotional/Vulnerable",
                        "Humorous/Playful",
                        "Critical/Harsh",
                        "Nostalgic/Sentimental",
                        "Controversial/Provocative",
                        "Aggressive/Hostile",
                        "Sympathetic/Supportive",
                        "Confused/Disoriented",
                        "Ambiguous/Uncertain",
                        "Formal/Professional",
                        "Casual/Informal"
                    ]
                },
                "minItems": 1,
                "maxItems": 2
            },
            "special_flags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "Potential backhanded compliment",
                        "Cultural/language ambiguity",
                        "Virtue signaling",
                        "Attention-seeking behavior",
                        "Multi-layered meaning",
                        "Hate Speech",
                        "Harmful",
                        "Emoji-Driven",
                        "Political/Religious Reference"
                    ]
                }
            },
            "reasoning": {
                "type": "object",
                "properties": {
                    "sentiment": {
                        "type": "string",
                        "description": "Explicit justification for sentiment classification"
                    },
                    "tone": {
                        "type": "string", 
                        "description": "Explanation of tone choices with examples"
                    },
                    "special_flags": {
                        "type": "string",
                        "description": "Explicit justification of any flagged elements"
                    }
                },
                "required": ["sentiment", "tone", "special_flags"]
            }
        },
        "required": ["sentiment", "tone", "special_flags", "reasoning"]
    }

@app.post("/analyze")
async def analyze_comment(request: Request):
    start_time = time.time()
    try:
        body = await request.json()
        logger.info(f"Incoming request body: {body}")
        
        comment_base = body.get("comment")
        # preserve special characters in the comment: Single quotes (') Double quotes (") Percent signs (%) Curly braces ({}) Backticks (`)  Newlines (\n) Escape characters (\)
        comment = json.dumps(comment_base)
        set_model = body.get("model", "llama3.2:1b")
        transcript_base = body.get("transcript", "")
        transcript = json.dumps(transcript_base)
        video_id = body.get("video_id")
        
        if not comment:
            logger.error("Comment is required")
            raise HTTPException(status_code=400, detail="Comment is required")

        # Include transcript context if available
        context_text = ""
        if transcript:
            context_text = f""" 
Your goal is to analyze and classify a comment based on a provided transcript
**Video Transcript Context**
{transcript} 

Using the above video transcript as context,
"""
            
        prompt = f"""
{context_text} analyze and classify the **YouTube COMMENT** using the multi-tier system below:

**Step 1: Primary Classification** 
Choose ONE main category from:
- Praise/Appreciation (content-specific)
- Constructive Criticism
- Video Quality Feedback
- Content Correction
- Personal Compliment (creator-focused)
- Creator Advice/Suggestion
- Collaboration Request
- Debate/Argumentation
- Shared Experience (personal stories, or situations that mirror the video’s themes)
- Inside Joke/Community Reference
- Technical Question
- Follow-Up Inquiry/Content Request (comments asking for specific topics or formats)
- Educational Addition
- Nostalgia/Throwback Reaction
- Cathartic Release
- Outrage/Moral Judgment
- Spam/Promotion (self-promotion, links or advertisements)
- Off-Topic
- Cultural Reference
- Meta Commentary (about platform/algorithm)
- Misinformation Flag (Identify factually incorrect claims)

**Step 2: Tone Analysis** 
Identify up to 2 tone aspects from:
- Enthusiastic/Hyperbolic
- Sarcastic/Ironic
- Neutral/Informative
- Emotional/Vulnerable 
- Humorous/Playful
- Critical/Harsh
- Nostalgic/Sentimental
- Controversial/Provocative
- Aggressive/Hostile
- Sympathetic/Supportive
- Confused/Disoriented
- Ambiguous/Uncertain
- Formal/Professional
- Casual/Informal

**Step 3: Special Flags** 
Mark if any apply:
- Potential backhanded compliment
- Cultural/language ambiguity
- Virtue signaling
- Attention-seeking behavior
- Multi-layered meaning
- Hate Speech
- Harmful
- Emoji-Driven
- Political/Religious Reference

**Response Requirements:**
1. JSON output following the schema
2. Concise reasoning covering:
- Key classification evidence
- Tone justification
- Contextual/cultural considerations
3. Flag special cases in reasoning

**YouTube Comment**:
"{comment}"
"""

        schema = create_schema()
        set_model = "mistral-small:22b" #"llama3.2:1b" #"qwen2.5:3b",#"mistral-small:22b",#"llama3.2:1b", #mistral-small:22b
        # for reproducibility
        seed = 1
        # context length
        num_ctx = 4096
        try:
            response = None
            response = ollama.generate(
            model=set_model,
            prompt= prompt,#prompt,
            format= schema, 
            options={
                "seed": seed,
                "num_ctx": num_ctx,
                },
            )

            result = json.loads(response['response'])


        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise HTTPException(status_code=503, detail="Ollama service unavailable")

        if (response.get('done', False)):
            print("successfull request")
            

            tone_str = "|".join(result.get('tone', []))
            special_flags_str = "|".join(result.get('special_flags', []))
            
            # Save results to CSV
            execution_time = time.time() - start_time
            save_to_csv(
                comment=comment,
                classification=result.get('sentiment'),
                tone=tone_str,
                special_flags=special_flags_str,
                reasoning=result.get('reasoning'),
                model=set_model,
                execution_time=execution_time,
                transcript_provided=bool(transcript),
                video_id=video_id,
                ollama_response=response,
                seed=seed,
                num_ctx=num_ctx
            )            
            

            return {
            "sentiment": result.get('sentiment'),
            "tone": result.get('tone', []),
            "special_flags": result.get('special_flags', []),
            "reasoning": result.get('reasoning')
        }
        else:
            raise HTTPException(status_code=500, detail="Error processing Ollama request")

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
            full_transcript = "\n".join([entry['text'] for entry in transcript])
            return {"transcript": full_transcript}
        except Exception as e:
            logger.error(f"Failed to get transcript: {e}")
            raise HTTPException(status_code=404, detail="Could not retrieve transcript")
            
    except Exception as e:
        logger.error(f"Error processing transcript request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    import uvicorn

    model_to_load = "mistral-small:22b"

    print("Loading the model ..")
    response = None
    response = ollama.generate(
        model= model_to_load,
        keep_alive = -1
    )
    
    if (response.get('done', False)):
        print("successfull loaded: ", model_to_load)
    else:
        print("failed request")

    uvicorn.run(app, host="0.0.0.0", port=8003)

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