import os
import io
import wave
import gradio as gr
import google.generativeai as genai
from google.cloud import speech
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro')

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
speech_client = speech.SpeechClient()


def handle_user_query(msg, chatbot):
    chatbot.append([msg, None])
    return '', chatbot


def generate_chatbot(chatbot):
    return [{"role": "model", "parts": [ch[1]]} for ch in chatbot if ch[1]]


def handle_gemini_response(chatbot):
    query = chatbot[-1][0]
    formatted_chatbot = generate_chatbot(chatbot[:-1])
    try:
        chat = model.start_chat(history=formatted_chatbot)
        response = chat.send_message(query)
        chatbot[-1][1] = response.text
    except Exception as e:
        chatbot[-1][1] = "Bir hata oluştu. Lütfen tekrar deneyin."
    return chatbot


def transcribe_audio(audio_path):
    with wave.open(audio_path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()

    with io.open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="tr-TR"
    )

    response = speech_client.recognize(config=config, audio=audio)
    if response.results:
        return response.results[0].alternatives[0].transcript
    return "Sesiniz anlaşılamadı."


# Gradio arayüzü
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label='Ders Asistanı')
    mesajKutusu = gr.Textbox(label="Mesaj Yazın")
    temizle = gr.Button("Temizle")
    gonderButonu = gr.Button("Gönder")
    mikrofon = gr.Audio(type="filepath", label="Sesli Komut")

    def clear_all():
        return [], ""

    temizle.click(clear_all, outputs=[chatbot, mesajKutusu])

    def send_message(message, chatbot):
        if not message:
            return chatbot, ""
        handle_user_query(message, chatbot)
        chatbot = handle_gemini_response(chatbot)
        return chatbot, ""

    def handle_audio(audio_file, chatbot):
        if audio_file is None:
            return chatbot, "Ses dosyası bulunamadı."
        transcription = transcribe_audio(audio_file)
        return send_message(transcription, chatbot)

    mesajKutusu.submit(send_message, inputs=[mesajKutusu, chatbot], outputs=[chatbot, mesajKutusu])
    gonderButonu.click(send_message, inputs=[mesajKutusu, chatbot], outputs=[chatbot, mesajKutusu])
    mikrofon.change(handle_audio, inputs=[mikrofon, chatbot], outputs=[chatbot, mesajKutusu])


if __name__ == "__main__":
    demo.launch()
