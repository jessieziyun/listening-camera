# Imports
import io
import os
import time
from dotenv import load_dotenv
from picamera2 import Picamera2
from vertexai import init
from vertexai.preview.vision_models import Image, ImageTextModel
import google.generativeai as genai
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.playback import play
from gradio_client import Client
from prompts import poet_prompt, film_composer_prompt

# Load environment variables
load_dotenv()

# Set up constants and initialize Vertex AI
output_dir = "output/"
PROJECT_ID = "listening-camera"
init(project=PROJECT_ID, location="europe-west2")
genai.configure(api_key=os.getenv("GOOGLEGENAI_API_KEY"))
huggingface_client = Client("zzyjn/create-audio", os.getenv("HF_TOKEN"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Initialize models
caption_model = ImageTextModel.from_pretrained("imagetext@001")
poem_model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize camera
camera = Picamera2()
camera.configure(camera.create_still_configuration())
camera.start()

def log_message(title: str, message: str):
    """Log messages in a formatted way."""
    print("\n" + "-" * 92)
    print(f"{title}:")
    print(message)
    print("-" * 92)

def capture_and_caption_image(timestamp):
    """Captures an image and returns its captions."""
    time.sleep(1)  # Allow time for the camera to adjust
    stream = io.BytesIO()
    
    # Capture and save the image
    camera.capture_file(stream, format='jpeg')
    file_name = f"{timestamp}_capture.jpg"
    camera.capture_file(os.path.join(output_dir, file_name))
    log_message("Captured Image", "Image has been captured successfully.")

    # Generate captions for the image
    source_img = Image(image_bytes=stream.getvalue())
    log_message("Generating Image Caption", "Retrieving captions for the captured image...")
    captions = caption_model.get_captions(image=source_img)
    log_message("Image Captions", "\n".join(captions))

    return captions

def write_poem(caption, timestamp):
    """Generates a poem based on the provided caption."""
    log_message("Generating Poem", "Creating a poem from the caption...")
    response = poem_model.generate_content(
        f"{poet_prompt}\n{caption}."
    )
    file_name = f"{timestamp}_poem.txt"
    with open(file_name, "w") as text_file:
        print(response.text, file=text_file)
    log_message("Generated Poem", response.text)
    return response.text  # Return the generated poem

def generate_soundtrack_description(poem, timestamp):
    response = poem_model.generate_content(f"{film_composer_prompt}\n*Input:*\n{poem}")
    file_name = f"{timestamp}_audio.txt"
    with open(file_name, "w") as text_file:
        print(response.text, file=text_file)
    log_message("Generated Audio Description", response.text)
    return response.text

def to_audio(prompt, timestamp):
    """Generates audio from text using the Hugging Face API."""
    try:
        log_message("Generating Audio", f"Sending poem to API...")
        result = huggingface_client.predict(prompt, api_name="/predict")
        log_message("Received Audio", str(result))

        # Export audio
        sound = AudioSegment.from_file(result, 'mp4')
        file_name = f"{timestamp}.mp3"
        output_path = os.path.join(output_dir, file_name)
        sound.export(output_path)
        # log_message("Audio File Saved", f"{output_path}: Audio was saved successfully!")
        return output_path
    except Exception as e:
        print(f"Error during audio generation: {str(e)}")
        raise

def generate_audio(timestamp):
    """Generates and plays audio based on the specified type."""
    # Capture image and generate captions
    caption = capture_and_caption_image(timestamp)
    
    # Generate poem from the caption
    poem = write_poem(caption, timestamp)
    audio_prompt = generate_soundtrack_description(poem, timestamp)
    audio_file = to_audio(audio_prompt, timestamp)

    # Play the generated audio file
    sound = AudioSegment.from_file(audio_file)
    log_message("Playing Audio", f"Playing {audio_file}")
    play(sound)
