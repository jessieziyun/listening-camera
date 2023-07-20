import os
from dotenv import load_dotenv
load_dotenv()

from gradio_client import Client

def load_space():
  HF_TOKEN = os.getenv("HF_TOKEN")
  client = Client("https://zzyjn-text-to-audio.hf.space/", HF_TOKEN)
  return client

def get_audio(client, text):
  result = client.predict(
    text,
    api_name="/predict"
  )
  return result
