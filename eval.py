from pptx import Presentation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import re

def extract_text_from_pptx(pptx_path):
    prs = Presentation(pptx_path)
    text_content = []
    
    for slide in prs.slides:
        slide_text = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                slide_text.append(shape.text.strip())
        text_content.append(" ".join(slide_text))
    
    return " ".join(text_content)

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_similarity(transcript_text, pptx_text):
    clean_transcript = clean_text(transcript_text)
    clean_pptx = clean_text(pptx_text)
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([clean_transcript, clean_pptx])
    
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return similarity_score

def analyze_content(transcript_path, pptx_path):
    with open(transcript_path, 'rb') as f:
        transcript_data = pickle.load(f)
    
    if isinstance(transcript_data, dict):
        transcript_text = ' '.join([item['text'] for item in transcript_data])
    else:
        transcript_text = ' '.join(transcript_data) if isinstance(transcript_data, list) else str(transcript_data)
    
    pptx_text = extract_text_from_pptx(pptx_path)
    
    similarity = calculate_similarity(transcript_text, pptx_text)
    return similarity

if __name__ == "__main__":
    transcript_path = "transcript.pkl"
    pptx_path = "output.pptx"
    
    similarity_score = analyze_content(transcript_path, pptx_path)
    print(f"Content Similarity Score: {similarity_score:.2f}")