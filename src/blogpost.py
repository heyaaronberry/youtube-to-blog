import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv
import subprocess
import json
from transformers import pipeline
from keyphrase_vectorizers import KeyphraseCountVectorizer
from keybert import KeyBERT

from src.editor import process_text, read_process_dict

current_dir = dirname(abspath(__file__))
dotenv_path = join(dirname(current_dir), '.env')
load_dotenv(dotenv_path)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

API_KEY = os.environ.get("DEEPGRAM_API_KEY")


class BlogPost():
    def __init__(self, video, output_dir):
        self.video = video
        self.text = None
        self.output_dir = output_dir
        self.transcription_data = None
        self.language_data = None 
        self.process_dict = self.load_process_dict()
        self.summary = None

    def transcribe_audio(self):
        try:
            print(f'Starting transcription')
            if not self.transcription_data:
                curl_command = [
                    "curl",
                    "--request", "POST",
                    "--header", f"Authorization: Token {API_KEY}",
                    "--header", "Content-Type: audio/mp3",
                    "--data-binary", f"@{self.video.get_audio_path()}",
                    "--url", "https://api.deepgram.com/v1/listen?paragraphs=true&punctuate=true"
                ]
                response = subprocess.run(curl_command, capture_output=True, text=True)
                transcript_json = response.stdout
                self.transcription_data = json.loads(transcript_json)
                print(f'Finished transcription')
            return self.transcription_data
        except Exception as e:
            print(f"Transcription Error: {e}")
            return None

    def get_text(self):
        try:
            if not self.text:
                if not self.transcription_data:
                    self.transcribe_audio()
                if self.transcription_data:
                    paragraphs_transcript = self.transcription_data['results']['channels'][0]['alternatives'][0]['paragraphs']['transcript']
                    processed_text = process_text(paragraphs_transcript, self.process_dict)
                    self.text = process_text(processed_text, self.process_dict)
            return self.text
        except Exception as e:
            print(f"Text Extraction Error: {e}")
        return None
    
    def generate_markdown_post(self):
        mardown_template = '''# {title}\n\n\{keywords}\n\n{summary}\n\n<img src="{image_name}" width="700"/>\n\n{text}'''

        mardown_post = mardown_template.format(
            title=self.video.get_title(),
            summary=self.summarize_transcript(),
            image_name=os.path.basename(self.video.get_image_path()),
            text=self.get_text(),
            keywords=self.get_keywords(3)
        )
        return mardown_post

    def save_markdown_post(self, mardown_post):
        print('Starting saving blog post')
        with open(self.get_md_path(), 'w', encoding='utf-8') as file:
            file.write(mardown_post)
        print('Finished saving blog post')

    def get_md_path(self):
        return os.path.join(self.output_dir, f'{self.video.get_base_name()}.md')
    
    def get_deepgram_summary(self):
        try:
            # Call deepgram_summarize_transcript to retrieve the Deepgram summary
            deepgram_summary = self.deepgram_summarize_transcript()
            # Check if deepgram_summary is not None and contains the expected structure
            if deepgram_summary and 'results' in deepgram_summary and 'summary' in deepgram_summary['results']:
                # Extract the short summary from deepgram_summary
                short_summary = deepgram_summary['results']['summary'].get('short', '')
                if short_summary:
                    # Process the short summary text if it's not empty
                    processed_text = process_text(short_summary, self.process_dict)
                    short_summary = processed_text
                    
                return short_summary  # Return the processed short summary
        except Exception as e:
            print(f"Exception: {e}")
        
        return None
    
    def deepgram_summarize_transcript(self):
        try:
            print("Deepgram summary request started")
            curl_command = [
                "curl",
                "--request", "POST",
                "--header", f"Authorization: Token {API_KEY}",
                "--header", "Content-Type: audio/mp3",
                 "--data-binary", f"@{self.video.get_audio_path()}",
                "--url", "https://api.deepgram.com/v1/listen?summarize=v2"
            ]
            response = subprocess.run(curl_command, capture_output=True, text=True)
            summary_json = response.stdout
            deepgram_summary = json.loads(summary_json)
            print("Deepgram summary request complete")
            return deepgram_summary
        except Exception as e:
            print(f"Deepgram Summarization Error: {e}")
            return None

    def summarize_transcript(self):
        try:
            if not self.summary:
                if not self.transcription_data:
                    self.transcribe_audio()
                if self.transcription_data:
                    transcript_text = self.transcription_data['results']['channels'][0]['alternatives'][0]['transcript']
                    summarized_text = process_text(transcript_text, self.process_dict)
                    
                    # Get the number of tokens in the summarized text
                    num_tokens = len(summarized_text.split())

                    if num_tokens > 1000:
                        print("Token input is greater than 1000, using Deepgram's summarization endpoint")
                        self.summary = self.get_deepgram_summary()
                    else:
                        print("Token input is less than or equal to 1000, using DistilBART summarization model")
                        summarizer = pipeline('summarization', model="sshleifer/distilbart-cnn-12-6")
                        self.summary = summarizer(summarized_text, max_length=150, min_length=40)[0]['summary_text'].replace(" .",".")
            return self.summary
        except Exception as e:
            print(f"Summarization Error: {e}")
            return None

    def load_process_dict(self):
        try:
            input_directory = 'input'
            process_dict_name = 'process_dictionary.json'
            process_dict_path = os.path.join(input_directory, process_dict_name)
            return read_process_dict(process_dict_path)
        except Exception as e:
            print(f"Process Dictionary Loading Error: {e}")
            return None

    def get_language(self):
        try:
            print("Starting language check")
            if not self.language_data:
                curl_command = [
                    "curl",
                    "--request", "POST",
                    "--header", f"Authorization: Token {API_KEY}",
                    "--header", "Content-Type: audio/mp3",
                    "--data-binary", f"@{self.video.get_audio_path()}",
                    "--url", "https://api.deepgram.com/v1/listen?model=nova-2-general&detect_language=true"
                ]
                response = subprocess.run(curl_command, capture_output=True, text=True)
                language_json = response.stdout
                language_data = json.loads(language_json)
                print("Finished language check")
                return language_data
        except Exception as e:
            print(f"Language Detection Error: {e}")
            return None

    def convert_language(self):
        try:
            language_data = self.get_language()
            if 'results' in language_data and 'channels' in language_data['results']:
                channels = language_data['results']['channels']
                if channels:
                    detected_language = channels[0].get('detected_language', '')
                    language_names = {
                        "en": "English",
                        "fr": "French",
                        # Add more language code to name mappings here
                    }
                    language_name = language_names.get(detected_language, "Unknown")
                    return language_name
                else:
                    print("No channels detected.")
                    return None
            else:
                print("No language data found in the response.")
                return None
        except Exception as e:
            print(f"Language Conversion Error: {e}")
            return None

    def get_keywords(self, n):
        try:
            print("Getting keywords...")
            keyword_model = KeyBERT()
            keywords = keyword_model.extract_keywords(
                docs=[self.get_text().replace('\n\n', '\n')],
                vectorizer=KeyphraseCountVectorizer()
            )
            if isinstance(keywords, list) and keywords:
                top_keywords = sorted(keywords, key=lambda t: t[1], reverse=True)[:n]
                processed_keywords = [f'#{keyword.replace(" ", "")}' for keyword, score in top_keywords]
                print("Finished getting keywords.")
                return ' '.join(processed_keywords)
            else:
                print("No keywords extracted or invalid format.")
                return None
        except Exception as e:
            print(f"Keyword Extraction Error: {e}")
            return None
