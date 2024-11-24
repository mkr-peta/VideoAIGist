import yt_dlp
import os

class YouTubeLoader:
    def __init__(self, output_dir: str = "temp"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def download_and_convert(self, url: str) -> str:
        try:
            temp_path = os.path.join(self.output_dir, "temp_audio")
            final_path = os.path.join(self.output_dir, "audio.mp3")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_path,  # Don't include extension
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',
                }],
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_path + ".mp3"):
                os.rename(temp_path + ".mp3", final_path)
            
            return final_path

        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")