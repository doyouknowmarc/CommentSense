import requests
import json
import csv
import time
import os
from datetime import datetime
import unicodedata

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

def save_model_results_to_csv(results, temperature, seed, num_ctx, output_file="model_analysis_results.csv"):
    # Create headers for the CSV
    headers = ['Comment']
    for model in results[list(results.keys())[0]]:
        headers.extend([
            f"{model} - Sentiment",
            f"{model} - Reasoning",
            f"{model} - Total Duration",
            f"{model} - Load Duration",
            f"{model} - Prompt Eval Count",
            f"{model} - Prompt Eval Duration",
            f"{model} - Eval Count",
            f"{model} - Eval Duration",
            f"{model} - Temperature",
            f"{model} - Seed",
            f"{model} - Num_ctx"
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
                    analysis.get('reasoning', 'N/A'),
                    format_duration(analysis.get('total_duration', 'N/A')),
                    format_duration(analysis.get('load_duration', 'N/A')),
                    analysis.get('prompt_eval_count', 'N/A'),
                    format_duration(analysis.get('prompt_eval_duration', 'N/A')),
                    analysis.get('eval_count', 'N/A'),
                    format_duration(analysis.get('eval_duration', 'N/A')),
                    temperature,
                    seed,
                    num_ctx
                ])
            writer.writerow(row)



def analyze(url, comments, model, temperature, seed, num_ctx):
    context = "\nVideo Transcript Context:\nall right this one got my attention for\n$500 the request the request how about\nyou learn how toing talk you all right\nthis one got my attention for $500 this\nrequest is for Dr Elana a\ntop cosmetic\ndentist in San Diego feels like I\'m\nadvertising pull a queen and an ace\ntogether from the\nwaterfall oh that\'s easy and then uh\nhave the King of Hearts Leap out of the\ndeck well we\'re going to have to fire up\nthe old CGI machines over there you guys\nhear that King from the deck um pulling\na queen and an ace together that\'s\npretty\neasy uh apparently doing running cuts to\nthe table is difficult because we just\ndrop some cards that\'s all right\nthen um let\'s make it\nhappen Ace and a queen together Shuff is\nlegit\nobviously uh nothing on top nothing on\nthe bottom no Ace Queen nothing in my\nhands um yeah you good Ace and queen let\nme just touch my face and palm of Ace\nand queen all right that\'s\neasy now this next\nbit uh getting a king of hearts the one\nand only King of Hearts to LEAP out of\nthe deck it\'s going to be difficult\nbecause generally cards don\'t leap out\nof a deck but we\'ll try this I\ncan\'t I wasn\'t really paying attention\nto how many times these cards were\nshuffled but we\'ll try something before\nwe continue only two\ncards I will push these cards into the\ndeck like\nthis and I will push down like this and\none card will\nleap from the top of the deck and that\nis in\nfact the king of\nI am so good anyway that\'s 500\nbucks\n$500 and uh if you\'re in San Diego and\nyou want a top cosmetic dentist there\'s\nonly one place to\ngo it\'s that easy\nfolks it\'s that that easy welcome to the\nhustle"
    results = {}
    counter = 1
    for comment in comments:
        print(f"Analyzing comment {counter}/{len(comments)} with model: {model}")
        counter += 1
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
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'format': {'type': 'object', 'properties': {'sentiment': {'enum': ['POSITIVE', 'NEUTRAL', 'NEGATIVE']}, 'reasoning': {'type': 'string'}}, 'required': ['sentiment', 'reasoning']},
            'options': {'temperature': temperature, 'seed': seed, 'num_ctx': num_ctx}}
        response = None

        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()  # This will raise an exception for bad status codes
        response_json = response.json()
        result = json.loads(response_json['response'])
        
        # Store results with metrics
        if comment not in results:
            results[comment] = {}
        results[comment][model] = {
            'sentiment': result['sentiment'],
            'reasoning': result['reasoning'],
            'total_duration': response_json.get('total_duration', 'N/A'),
            'load_duration': response_json.get('load_duration', 'N/A'),
            'prompt_eval_count': response_json.get('prompt_eval_count', 'N/A'),
            'prompt_eval_duration': response_json.get('prompt_eval_duration', 'N/A'),
            'eval_count': response_json.get('eval_count', 'N/A'),
            'eval_duration': response_json.get('eval_duration', 'N/A')
        }
      
    return results



# Main process
def main():
    start_time_total = time.time()
    # Define the Ollama API endpoint
    url = "http://localhost:11434/api/generate" 
    temperature = 0
    seed = 1
    num_ctx =  8192

    # Define the path to the comments CSV file
    filepath_comments_csv = "../ModelAnalysis/UserEvaluationStudy_20_Comments.csv"

# Read the CSV file and clean comments
    cleaned_comments = []
    with open(filepath_comments_csv, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file, quotechar='"')  # Use quotechar to handle quoted fields
        next(reader)  # Skip the header
        for row in reader:
            # Join the row into a single string (in case it was split by commas)
            comment = " ".join(row)
            # Clean the comment
            cleaned_comment = clean_string(comment)
            # Add to the cleaned comments list
            cleaned_comments.append(cleaned_comment)

    # Print the cleaned comments
    for comment in cleaned_comments:
        print(comment)


    slms = [
        "qwen2.5:0.5b",
        "qwen2.5:1.5b",
        "qwen2.5:3b", 
        "llama3.2:1b",
        "llama3.2:3b",
        "internlm2:1.8b",
        "deepseek-r1:1.5b",
        "smollm2:135m",
        "smollm2:360m",
        "smollm2:1.7b",
        "gemma2:2b",
        "qwen2.5:7b",
        "phi3.5",
        "mistral-small:22b",
        "phi4",
        "deepseek-r1:7b",
        "deepseek-r1:8b",
        "gemma2:9b",
        "internlm2:7b",
        "gemma3",
        "gemma3:1b",
    ]


    for model in slms:
        start_time_model = time.time()
       # payload = {
        #    'model': model,
        #    'keep_alive': -1,
        #    'stream': False,
        #    'options': {'temperature': temperature, 'seed': seed, 'num_ctx': num_ctx}}
        #response = None
        #response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        print(f"-- Analyzing comments using model: {model} --")

        results = analyze(url, cleaned_comments, model, temperature, seed, num_ctx)
        # Save individual model results
        save_model_results_to_csv(results, temperature, seed, num_ctx, f"single_model_analysis_{model.replace(':', '_')}.csv")


        print("Analysis complete.")
        payload = {
            'model': model,
            'keep_alive': 0,
            'stream': False,
            'options': {'temperature': temperature, 'seed': seed, 'num_ctx': num_ctx}}
        response = None
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        print(response)
        print(f"-- {model} model has been stopped. --\n \n")
        model_duration = time.time() - start_time_model
        print(f"Time taken for {model}: {model_duration:.2f} seconds")
    
    
    total_duration = time.time() - start_time_total
    print(f"\nTotal execution time: {total_duration:.2f} seconds")

# Run the main process
if __name__ == '__main__':
    main()