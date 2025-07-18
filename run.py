import gradio as gr
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from gradio_ui import demo

load_dotenv()

app = FastAPI()


@app.get("/")
async def home():
    return JSONResponse({"message": "Gradio UI is running at /gradio"}, status_code=200)


app = gr.mount_gradio_app(app, demo, path="/gradio")
