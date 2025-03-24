from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import csv
from datetime import datetime
from transformers import pipeline
import time

import os

# Path to the CSV file
CSV_FILE = os.path.join(os.path.dirname(__file__), "analyzed_comments_bert_sentiment.csv")

# Ensure the directory exists
os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

def save_to_csv(comment, sentiment, confidence=None, model=None, execution_time=None):
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow([
                "Timestamp", "Comment", "Classification", "Type", 
                "Confidence", "Model", "ExecutionTime"
            ])
        # Write the comment data with execution time
        writer.writerow([
            datetime.now().isoformat(),
            comment,
            sentiment,
            "sentiment",
            confidence,
            model,
            f"{execution_time:.2f}" if execution_time is not None else None
        ])

# Create a FastAPI instance
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allow CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for testing)
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# Load the BERT sentiment analysis pipeline
bert_sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@app.post("/analyze")
async def analyze_comment(request: Request):
    start_time = time.time()
    try:
        body = await request.json()
        logger.info(f"Incoming request body: {body}")
        
        comment = body.get("comment")
        
        if not comment:
            logger.error("Comment is required")
            raise HTTPException(status_code=400, detail="Comment is required")
        # Use BERT for sentiment analysis
        logger.info("Using BERT (DistilBERT) for sentiment analysis")

        # Analyze the comment using BERT
        result = bert_sentiment_pipeline(comment)[0]
        sentiment = result["label"].upper()
        confidence = result["score"]

        logger.info(f"BERT sentiment analysis result: {sentiment}, Confidence: {confidence}")

        # Save the comment and analysis result to a CSV file
        execution_time = time.time() - start_time
        save_to_csv(
            comment=comment, 
            sentiment=sentiment, 
            confidence=confidence, 
            model="distilbert-base-uncased-finetuned-sst-2-english", 
            execution_time=execution_time
        )

        # Return sentiment and confidence to the Chrome extension
        return {"sentiment": sentiment, "confidence": confidence}


    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error analyzing comment: {str(e)}. Execution time: {execution_time:.2f}s")
        raise HTTPException(status_code=500, detail=str(e))

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)