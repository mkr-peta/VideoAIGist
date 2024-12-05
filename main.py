from src.transcription import VideoTranscriptionService
from secret_keys import get_open_ai_key, get_anthropic_key
from src.content_processing import ContentAnalyzer
from src.presentation import SlideGenerator
from src.image_service import ImageGenerator
import os
import pickle
import re
import urllib.request
import json

def extract_youtube_title(url):
    try:
        video_id = None
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        
        if not video_id:
            return None
            
        params = {"format": "json", "url": f"https://www.youtube.com/watch?v={video_id}"}
        url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}"
        
        with urllib.request.urlopen(url) as response:
            response_text = response.read()
            data = json.loads(response_text.decode())
            return data['title']
    except Exception as e:
        print(f"Could not extract title: {e}")
        return None

def get_user_input():
    """Get user input for presentation parameters."""
    youtube_url = input("Enter the YouTube video URL: ").strip()
    num_slides = int(input("Enter the desired number of slides: ").strip())
    num_images = int(input("Enter the number of images to generate (0 for no images): ").strip())
    output_filename = input("Enter the output PowerPoint filename (without .pptx): ").strip()
    
    if not output_filename.endswith('.pptx'):
        output_filename += '.pptx'
        
    return youtube_url, num_slides, num_images, output_filename

def main():
    api_key = get_open_ai_key()
    claude_api_key = get_anthropic_key()
    os.environ['ANTHROPIC_API_KEY'] = claude_api_key

    service = VideoTranscriptionService(api_key=api_key)
    image_generator = ImageGenerator(
        api_key=api_key,
        output_dir="temp_images"
    )
    
    try:
        youtube_url, num_slides, num_images, output_filename = get_user_input()
        
        analyzer = ContentAnalyzer(api_key=claude_api_key, num_slides=num_slides)
        slide_generator = SlideGenerator()

        presentation_title = extract_youtube_title(youtube_url)
        if not presentation_title:
            presentation_title = "YouTube Video Summary"

        try:
            transcript = service.transcribe_youtube_video(
                url=youtube_url,
                language="en"
            )
            
            with open("transcript.pkl", "wb") as f:
                pickle.dump(transcript, f)
                
        except Exception as e:
            print(f"Error getting transcript: {e}")
            print("Attempting to load from backup...")
            transcript = pickle.load(open("transcript.pkl", "rb"))

        slides = analyzer.analyze_transcript(transcript)

        if num_images > 0:
            slide_scores = [(i, image_generator.analyze_slide_worthiness(slide)) 
                          for i, slide in enumerate(slides)]
            top_slides = sorted(slide_scores, key=lambda x: x[1], reverse=True)[:num_images]

            for slide_index, score in top_slides:
                slide = slides[slide_index]
                prompt = image_generator.generate_image_prompt(slide)
                image_path = image_generator.generate_and_save_image(prompt, slide_index)
                slides[slide_index]['image_path'] = image_path
                print(f"Generated image for slide {slide_index + 1}")

        slide_generator.generate_presentation(
            slides_content=slides,
            output_path=output_filename,
            presentation_title=presentation_title
        )
        print(f"Presentation generated successfully as '{output_filename}'!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()