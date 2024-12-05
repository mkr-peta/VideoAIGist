import streamlit as st
from src.transcription import VideoTranscriptionService
from secret_keys import get_open_ai_key, get_anthropic_key
from src.content_processing import ContentAnalyzer
from src.presentation import SlideGenerator
from src.image_service import ImageGenerator
import os
import pickle
import urllib.request
import json

def extract_youtube_title(url):
    """Extract the title of a YouTube video from its URL."""
    try:
        video_id = None
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        
        if not video_id:
            return None
            
        url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}"
        with urllib.request.urlopen(url) as response:
            response_text = response.read()
            data = json.loads(response_text.decode())
            return data['title']
    except Exception as e:
        st.warning(f"Could not extract title: {e}")
        return None

def create_app():
    st.title("VideoAIGist - YouTube Video to PowerPoint")
    
    # Input fields
    youtube_url = st.text_input("YouTube Video URL")
    num_slides = st.number_input("Number of Slides", min_value=1, value=10)
    num_images = st.number_input("Number of Images (0 for no images)", min_value=0, value=1)
    output_filename = st.text_input("Output PowerPoint filename", value="output.pptx")
    
    if not output_filename.endswith('.pptx'):
        output_filename += '.pptx'

    if st.button("Generate PowerPoint"):
        if youtube_url:
            try:
                with st.spinner("Initializing..."):
                    # Get API keys
                    api_key = get_open_ai_key()
                    claude_api_key = get_anthropic_key()
                    os.environ['ANTHROPIC_API_KEY'] = claude_api_key

                    # Initialize services
                    service = VideoTranscriptionService(api_key=api_key)
                    image_generator = ImageGenerator(api_key=api_key, output_dir="temp_images")
                    analyzer = ContentAnalyzer(api_key=claude_api_key, num_slides=num_slides)
                    slide_generator = SlideGenerator()

                    # Get video title
                    presentation_title = extract_youtube_title(youtube_url)
                    if not presentation_title:
                        presentation_title = "YouTube Video Summary"

                with st.spinner("Transcribing video..."):
                    try:
                        transcript = service.transcribe_youtube_video(url=youtube_url, language="en")
                        with open("transcript.pkl", "wb") as f:
                            pickle.dump(transcript, f)
                    except Exception as e:
                        st.warning("Error getting transcript, attempting to load from backup...")
                        transcript = pickle.load(open("transcript.pkl", "rb"))

                with st.spinner("Analyzing content..."):
                    slides = analyzer.analyze_transcript(transcript)

                if num_images > 0:
                    with st.spinner("Generating images..."):
                        slide_scores = [(i, image_generator.analyze_slide_worthiness(slide)) 
                                      for i, slide in enumerate(slides)]
                        top_slides = sorted(slide_scores, key=lambda x: x[1], reverse=True)[:num_images]

                        progress_bar = st.progress(0)
                        for idx, (slide_index, score) in enumerate(top_slides):
                            slide = slides[slide_index]
                            prompt = image_generator.generate_image_prompt(slide)
                            image_path = image_generator.generate_and_save_image(prompt, slide_index)
                            slides[slide_index]['image_path'] = image_path
                            progress_bar.progress((idx + 1) / len(top_slides))

                with st.spinner("Generating PowerPoint..."):
                    slide_generator.generate_presentation(
                        slides_content=slides,
                        output_path=output_filename,
                        presentation_title=presentation_title
                    )

                # Provide download link
                if os.path.exists(output_filename):
                    with open(output_filename, "rb") as file:
                        st.download_button(
                            label="Download PowerPoint",
                            data=file,
                            file_name=output_filename,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
                    st.success("PowerPoint generated successfully!")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a YouTube URL")

if __name__ == "__main__":
    create_app()