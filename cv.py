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
    print("\n" + "-" * 40)
    print(f"{title}:")
    print(message)
    print("-" * 40)

def capture_and_caption_image():
    """Captures an image and returns its captions."""
    time.sleep(1)  # Allow time for the camera to adjust
    stream = io.BytesIO()
    
    # Capture and save the image
    camera.capture_file(stream, format='jpeg')
    file_name = f"{int(time.time())}_capture.jpg"
    camera.capture_file(os.path.join(output_dir, file_name))
    log_message("Captured Image", "Image has been captured successfully.")

    # Generate captions for the image
    source_img = Image(image_bytes=stream.getvalue())
    log_message("Generating Image Caption", "Retrieving captions for the captured image...")
    captions = caption_model.get_captions(image=source_img)
    log_message("Image Captions", "\n".join(captions))

    return captions

def write_poem(caption):
    """Generates a poem based on the provided caption."""
    log_message("Generating Poem", "Creating a poem from the caption...")
    response = poem_model.generate_content(
        f"You are a world-class poet. Write a poem inspired by this scene: {caption}."
    )
    log_message("Generated Poem", response.text)
    return response.text  # Return the generated poem

def text_to_speech_file(text: str) -> str:
    """Converts text to speech and saves it to an MP3 file."""
    log_message("Generating Audio", "Converting text to speech...")
    response = elevenlabs_client.text_to_speech.convert(
        voice_id="pFZP5JQG7iQjIQuC4Bku",  # Lily pre-made voice
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",  # Use turbo model for low latency
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    file_name = f"{int(time.time())}_tts.mp3"
    save_file_path = os.path.join(output_dir, file_name)

    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    log_message("Audio File Saved", f"{save_file_path}: Audio file saved successfully!")
    return save_file_path

def to_audio(text):
    """Generates audio from text using the Hugging Face API."""
    try:
        log_message("Generating Audio", f"Sending text to API: {text}")
        result = huggingface_client.predict(text, api_name="/predict")
        log_message("Raw API Response", str(result))

        # Export audio
        sound = AudioSegment.from_file(result, 'mp4')
        file_name = f"{int(time.time())}_audio.mp3"
        output_path = os.path.join(output_dir, file_name)
        sound.export(output_path)
        log_message("Audio File Saved", f"{output_path}: Audio was saved successfully!")
        return output_path
    except Exception as e:
        print(f"Error during audio generation: {str(e)}")
        raise

def generate_audio(audio_type: str):
    """Generates and plays audio based on the specified type."""
    # Capture image and generate captions
    caption = capture_and_caption_image()
    
    # Generate poem from the caption
    poem = write_poem(caption)

    if audio_type == "tts":
        audio_file = text_to_speech_file(poem)
    elif audio_type == "audio":
        audio_file = to_audio(poem)
    else:
        raise ValueError("Invalid audio_type. Must be 'tts' or 'audio'.")

    # Play the generated audio file
    sound = AudioSegment.from_file(audio_file)
    play(sound)
    log_message("Playing Audio", f"Playing {audio_type} audio from file: {audio_file}")
