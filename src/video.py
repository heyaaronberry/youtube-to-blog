import re
import os
import subprocess
import requests
from pytube import YouTube

from src.editor import crop_image_border, save_image

class Video:
    def __init__(self, url, output_dir):
        self.youtube = YouTube(url)
        self.output_dir = output_dir

    def clean_output_dir(self):
        print("Cleaning output directory...")
        # Iterate over files in the output directory and delete them
        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")    

    def get_title(self):
        return self.youtube.streams[0].title
    
    def get_slug(self):
        title = self.get_title()
        slug = re.sub(r'[^\w]+', '-', title.lower())  # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r'[-]+', '-', slug)  # Replace multiple hyphens with a single hyphen
        slug = slug.strip('-')  # Remove leading and trailing hyphens
        return slug

    def get_base_name(self):
        return re.sub(r'[^0-9a-zA-Z]+', '', self.get_title()) 

    def get_audio_path(self):
        return self.__get_path('{}.mp3')  

    def get_image_path(self):
        return self.__get_path('{}.png') 
    
    def get_url(self):
        return f"https://www.youtube.com/watch?v={self.youtube.video_id}"

    def get_video_length(self):
        # Convert the video length from seconds to minutes
        minutes = round(self.youtube.length / 60)

        # If the video is more than 60 minutes, convert to hours
        if minutes >= 60:
            hours = minutes // 60
            return f"{hours} {'hour' if hours == 1 else 'hours'}"
        else:
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'}"
        
    def __get_path(self, extension_str):
        return os.path.join(self.output_dir, extension_str.format(self.get_base_name()))
    
    def clean_filename(self, filename):
        # Remove spaces and trailing punctuation marks from the filename
        cleaned_filename = re.sub(r'\s+', '', filename.strip())
        cleaned_filename = re.sub(r'[^\w\s]', '', cleaned_filename)
        return cleaned_filename

    def download_thumbnail(self):
        print("Starting thumbnail download...")
        # Check if thumbnail already exists in the output directory
        thumbnail_file_name = f"{self.clean_filename(self.get_title())}.png"
        thumbnail_path = os.path.join(self.output_dir, thumbnail_file_name)
        if os.path.exists(thumbnail_path):
            print("Thumbnail already exists. Skipping download.")
            return thumbnail_path  # Return the path to the existing thumbnail
        
        # Thumbnail doesn't exist, proceed with download
        thumbnail_url = f"https://i.ytimg.com/vi/{self.youtube.video_id}/hqdefault.jpg"
        thumbnail_image = requests.get(thumbnail_url).content
        cropped_image = crop_image_border(thumbnail_image)
        save_image(cropped_image, thumbnail_path)
        print("Finished downloading thumbnail")
        print(f"Image path: {thumbnail_path}")
        return thumbnail_path

    def convert_to_mp3(self):
        print("starting mp3 conversion...")
        self.clean_output_dir()
        cleaned_title = self.clean_filename(self.get_title())
        mp3_output_path = os.path.join(self.output_dir, f"{cleaned_title}.mp3")
        
        # Check if MP3 file already exists in the output directory
        if os.path.exists(mp3_output_path):
            print("MP3 file already exists. Skipping conversion.")
            return mp3_output_path  # Return the path to the existing MP3 file
        
        # MP3 file doesn't exist, proceed with conversion
        command = ['ffmpeg', '-i', self.youtube.streams.get_highest_resolution().url, '-vn', '-acodec', 'libmp3lame', '-fs', '2G', mp3_output_path]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Finished converting to MP3")
        print(f"MP3 output path: {mp3_output_path}")
        return mp3_output_path 
