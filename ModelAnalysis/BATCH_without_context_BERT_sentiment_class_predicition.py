import requests
import json
import csv
import time
import os
from datetime import datetime
import unicodedata
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
from torch.nn.functional import softmax
import numpy as np

# Initialize DistilBERT model and tokenizer
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased-finetuned-sst-2-english')


# Function to clean a single string
def clean_string(s):
    s = s.replace("\xa0", " ")  # Replace \xa0 with a space
    s = s.rstrip(";")  # Remove trailing semicolons
    s = unicodedata.normalize("NFKC", s)  # Normalize Unicode characters
    s = s.strip()  # Remove leading/trailing whitespace
    return s


def load_existing_comments(filename):
    comments = []
    if os.path.exists(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            for row in reader:
                comments.append(row)
    return comments


def format_duration(duration):
    if duration == 'N/A':
        return 'N/A'
    # Convert nanoseconds to seconds and format with 2 decimal places
    return f"{duration / 1e9:.2f}"

def save_model_results_to_csv(results, output_file="model_analysis_results22.csv"):
    # Create headers for the CSV
    headers = ['Comment']
    for model in results[list(results.keys())[0]]:
        headers.extend([
            f"{model} - Sentiment",
            f"{model} - Reasoning"
        ])
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        # Write comment analysis results
        for comment, model_results in results.items():
            row = [comment]
            for model, analysis in model_results.items():
                row.extend([
                    analysis.get('sentiment', 'N/A'),
                    analysis.get('reasoning', 'N/A')
                ])
            writer.writerow(row)

def analyze(comments):
    results = {}
    device = torch.device('mps' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    model.eval()
    
    for counter, comment in enumerate(comments, 1):
        print(f"Analyzing comment {counter}/{len(comments)}")
        
        # Tokenize and prepare input
        inputs = tokenizer(comment, return_tensors="pt", truncation=True, max_length=512, padding=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        start_time = time.time()
        
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = softmax(outputs.logits, dim=-1)
            
        # Convert predictions to sentiment labels (SST-2 is binary: negative=0, positive=1)
        sentiment_scores = predictions[0].cpu().numpy()
        sentiment_label = 'POSITIVE' if np.argmax(sentiment_scores) == 1 else 'NEGATIVE'
        
        # Calculate confidence scores
        confidence_scores = {
            'NEGATIVE': float(sentiment_scores[0]),
            'POSITIVE': float(sentiment_scores[1])
        }
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Store results
        if comment not in results:
            results[comment] = {}
        
        results[comment]['distilbert-sst2'] = {
            'sentiment': sentiment_label,
            'reasoning': f"Confidence scores - Negative: {confidence_scores['NEGATIVE']:.3f}, Positive: {confidence_scores['POSITIVE']:.3f}"
        }
    
    return results



# Main process
def main():
    start_time_total = time.time()
    
    # Define the path to the comments CSV file
    filepath_comments_csv = "UserEvaluationStudy_20_Comments.csv"

    # Read and clean comments
    cleaned_comments = []
    with open(filepath_comments_csv, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file, quotechar='"')
        next(reader)  # Skip the header
        for row in reader:
            comment = " ".join(row)
            cleaned_comment = clean_string(comment)
            cleaned_comments.append(cleaned_comment)

    print("Analyzing comments using DistilBERT...")
    results = analyze(cleaned_comments)
    
    # Save results
    save_model_results_to_csv(results, "model_analysis_distilbert.csv")
    
    total_duration = time.time() - start_time_total
    print(f"\nTotal execution time: {total_duration:.2f} seconds")

if __name__ == '__main__':
    main()