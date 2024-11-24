from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate

class ContentAnalyzer:
    def __init__(self, api_key: str, num_slides: int):
        self.llm = ChatAnthropic(model="claude-3-opus-20240229")
        self.num_slides = num_slides
        
        # Outline prompt remains same
        self.outline_prompt = ChatPromptTemplate.from_template("""
            Analyze this transcript and create exactly {num_slides} main sections.
            Make sure that all the content that you generate is relevant to and from the transcript.
            
            Your response MUST follow this EXACT format for each section:
            SECTION: [section title]
            KEY POINTS:
            - [key point 1]
            - [key point 2]
            - [key point 3]
            - [Key point 4]
            - [Key point 5 if needed]
            
            Each section MUST have:
            - A clear, descriptive title
            - At least 3 key points
            - All content directly from the transcript
            
            Transcript: {transcript}
        """)

    def _validate_slide_content(self, slide_content: dict) -> bool:
        has_title = bool(slide_content['title'])
        has_points = len(slide_content['points']) >= 3  # Require at least 3 substantial points
        has_notes = len(slide_content['speaker_notes']) >= 1
        return has_title and has_points and has_notes

    def _create_outline(self, transcript: str) -> list[dict]:
        # This method remains exactly same as before
        response = self.llm.invoke(
            self.outline_prompt.format(
                num_slides=self.num_slides,
                transcript=transcript
            )
        )
        
        response_text = response.content
        sections = []
        current_section = {}

        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('SECTION:'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line.replace('SECTION:', '').strip(),
                    'key_points': []
                }
            elif line.startswith('-'):
                point = line[1:].strip()
                if point:
                    current_section['key_points'].append(point)

        if current_section:
            sections.append(current_section)

        return sections

    def _parse_slide_content(self, response_text: str) -> dict:
        slide_content = {
            'title': '',
            'points': [],
            'speaker_notes': []  # Changed from 'details' to 'speaker_notes'
        }
        
        current_section = None
        for line in response_text.split('\n'):
            line = line.strip()
            if 'TITLE:' in line:
                slide_content['title'] = line.replace('TITLE:', '').strip()
            elif 'SLIDE CONTENT:' in line:
                current_section = 'points'
            elif 'SPEAKER NOTES:' in line:
                current_section = 'speaker_notes'
            elif line.startswith('-') and current_section:
                content = line[1:].strip()
                if content:
                    slide_content[current_section].append(content)
                    
        return slide_content

    def _extract_detailed_content(self, sections: list[dict]) -> list[dict]:
        detailed_slides = []

        for section in sections:
            prompt = f"""
                Create presentation slide content for this section.
                Section: {section['title']}
                Key Points: {'\n'.join(section['key_points'])}

                Your response MUST follow this EXACT format:
                TITLE: [clear, concise title]
                
                SLIDE CONTENT:
                - [comprehensive bullet point (1-2 lines)]
                - [comprehensive bullet point (1-2 lines)]
                - [comprehensive bullet point (1-2 lines)]
                - [comprehensive bullet point (1-2 lines)]
                - [optional fourth point if needed]
                
                SPEAKER NOTES:
                - [additional context/details for presenter]
                - [examples or elaboration]

                Requirements:
                - Each SLIDE CONTENT point must be a complete, informative statement
                - 4-5 substantial points per slide
                - Points should be presentation-friendly and readable
                - Speaker notes should provide additional context
                - All content must come from the transcript
            """

            response = self.llm.invoke(
                ChatPromptTemplate.from_template(prompt).format_messages(
                    section_title=section['title'],
                    key_points='\n'.join(section['key_points'])
                )
            )

            slide_content = self._parse_slide_content(response.content)
            
            if not self._validate_slide_content(slide_content):
                print(f"Retrying content generation for section: {section['title']}")
                retry_prompt = prompt + "\nPrevious attempt was incomplete. Please ensure all required sections are included."
                response = self.llm.invoke(ChatPromptTemplate.from_template(retry_prompt))
                slide_content = self._parse_slide_content(response.content)
            
            detailed_slides.append(slide_content)

        return detailed_slides

    def analyze_transcript(self, transcript: str) -> list[dict]:
        print("Creating outline...")
        outline = self._create_outline(transcript)

        # print("Generated Outline:")
        # for section in outline:
        #     print(f"Section Title: {section['title']}")
        #     print("Key Points:")
        #     for point in section['key_points']:
        #         print(f" - {point}")
        #     print("=" * 50)
        
        print("Extracting detailed content...")
        slides = self._extract_detailed_content(outline)

        print("\nGenerated Slides Content:")
        print("=" * 50)
        for i, slide in enumerate(slides, 1):
            print(f"\nSlide {i}: {slide['title']}")
            print("\nSlide Content:")
            for point in slide['points']:
                print(f"• {point}")
            print("\nSpeaker Notes:")
            for note in slide['speaker_notes']:
                print(f"→ {note}")
            print("=" * 50)
        
        return slides