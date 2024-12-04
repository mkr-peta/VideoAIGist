from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO
import os

class ImageGenerator:
    def __init__(self, api_key: str, output_dir: str = "temp_images"):
        self.client = OpenAI(api_key=api_key)
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)


    def analyze_slide_worthiness(self, slide_content: dict) -> float:
        prompt = f"""
        Rate this slide's need for an image from 0 to 1.
        Title: {slide_content['title']}
        Content: {' '.join(slide_content['points'])}
        Consider:
        - How abstract/technical is the content?
        - Would visualization enhance understanding?
        - Is it a key concept that benefits from illustration?
        Return only the numerical score.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        return float(response.choices[0].message.content.strip())
    

    def generate_image_prompt(self, slide_content: dict) -> str:
        prompt = f"""
            Create a DALL-E prompt for visualizing this slide's content:
            Title: {slide_content['title']}
            Content: {' '.join(slide_content['points'])}
            Context: {' '.join(slide_content['speaker_notes'])}

            Requirements for the image:
            - Must directly illustrate the key concepts from the slide
            - Should help viewers better understand the slide content
            - Focus on clear, educational visualization
            - Professional and minimalistic style
            - Suitable for business presentation
            - Clean and modern design
            - No text in the image
            - Use subtle, professional colors

            The image should serve as a visual aid that enhances understanding of:
            1. The main topic: {slide_content['title']}
            2. The key points being presented
            
            Return only the DALL-E prompt.
            """
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    

    def generate_and_save_image(self, prompt: str, index: int) -> str:
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        image_path = os.path.join(self.output_dir, f"slide_image_{index}.png")
        
        # Download and save image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        img.save(image_path)
        
        return image_path