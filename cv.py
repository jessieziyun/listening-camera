#imports
import io
import os
import time
import requests
from dotenv import load_dotenv
import openai
from google.cloud import vision
from picamera2 import Picamera2
from pydub import AudioSegment
from pydub.playback import play
from gradio_client import Client

#load env
load_dotenv()

#set up camera
camera = Picamera2()
capture_config = camera.create_still_configuration()
camera.configure(camera.create_preview_configuration())
camera.start()

#capture image to stream
def capture_image():
  time.sleep(1)
  stream = io.BytesIO()
  camera.capture_file(stream, format='jpeg')
  print("Captured image")
  return stream

#get image labels
def get_labels():
  stream = capture_image()
  client = vision.ImageAnnotatorClient()
  content = stream.getvalue()
  image = vision.Image(content=content)
  response = client.label_detection(image=image)
  labels = response.label_annotations
  image_labels = "\n".join(str(label.description) for label in labels)
  return image_labels

#generate a haiku from image labels
def generate_haiku():
  image_labels = get_labels()
  openai.api_key = os.getenv("OPENAI_API_KEY")
  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "user", "content": "Using the following words as inspiration, write a haiku.\n"+image_labels}
    ]
  )
  return completion.choices[0].message.content

def to_speech(text):
  CHUNK_SIZE = 1024
  voice_id = "21m00Tcm4TlvDq8ikWAM"
  url = "https://api.elevenlabs.io/v1/text-to-speech/" + voice_id
  headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
  }
  data = {
    "text": text,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
      "stability": 0,
      "similarity_boost": 0
    }
  }
  response = requests.post(url, json=data, headers=headers)
  stream = io.BytesIO()
  for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
    if chunk:
      stream.write(chunk)
  stream.seek(0)
  sound = AudioSegment.from_file(stream, 'mp3')
  play(sound)

def load_space():
  HF_TOKEN = os.getenv("HF_TOKEN")
  client = Client("https://zzyjn-text-to-audio.hf.space/", HF_TOKEN)
  return client

def to_audio(client, text):
  result = client.predict(
    text,
    api_name="/predict"
  )
  sound = AudioSegment.from_file(result, 'mp4')
  play(sound)
