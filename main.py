import argparse
import os
from src.video import Video
from src.blogpost import BlogPost

def transcribe_and_create_post(video_url):
    try:
        print(f'Youtube URL: {video_url}')
        
        # Create output directory if it doesn't exist
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Initialize video, blog post, and WordPress objects
        video = Video(video_url, output_dir)
        video.convert_to_mp3()
        video.download_thumbnail()

        blog_post = BlogPost(video, output_dir)
        markdown_post = blog_post.generate_markdown_post()
        blog_post.save_markdown_post(markdown_post)
        # Transcribe the video and get transcription data
        transcription_data = blog_post.transcribe_audio()
        
        # Return transcription response immediately
        response = {
            'message': 'Transcription data available',
            'url': video_url,
            'transcription_data': transcription_data
        }
        
        return response, 200
    
    except Exception as e:
        # Handle exceptions
        return {'error': str(e)}, 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transcribe and create blog post from a video URL')
    parser.add_argument('video_url', type=str, help='URL of the video')
    args = parser.parse_args()

    result, status = transcribe_and_create_post(args.video_url)
    print(result)
