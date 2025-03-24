from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Create a formatted transcript text
        transcript_text = ''
        for entry in transcript:
            transcript_text += f"{entry['text']}\n"
        
        # Write to file
        with open(f'transcript_{video_id}.txt', 'w', encoding='utf-8') as file:
            file.write(transcript_text)
            
        print(f"Transcript has been saved to transcript_{video_id}.txt")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Get transcript for the specified video
video_id = "" # Add the video ID here
get_transcript(video_id)