"""
Chainlit + Groq Application (Morpheus AI)
--------------------------------------------------------------
Ye script Chainlit ko Groq ke AI models se jodta hai.
"""

# 1️⃣ Importing Required Libraries
import os
import asyncio
import pymupdf as fitz
import time

import io
from chainlit.element import ElementBased

import wave

from groq import Groq
from openai import OpenAI
from google import genai
from docx import Document
from dotenv import load_dotenv
from typing import Dict, Optional

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.input_widget import Select, Switch
from chainlit.types import ThreadDict

# 2️⃣ Load Environment Variables and Define Global Variables
load_dotenv()

models = ['groq/compound', 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant']


# 3️⃣ Client Setup
groq_api_key = os.getenv("GROQ_API_KEY") or "placeholder_groq_key"
openai_api_key = os.getenv("OPENAI_API_KEY") or "placeholder_openai_key"
gemini_api_key = os.getenv("GEMINI_API_KEY") or "placeholder_gemini_key"

groq_client = Groq(api_key=groq_api_key)
openai_client = OpenAI(api_key=openai_api_key)
try:
    gemini_client = genai.Client(api_key=gemini_api_key)
except Exception:
    gemini_client = None

# Kaunsa model kis company ka hai, ye batane wali dictionary
model_provider = {
    'groq/compound': 'groq',
    'llama-3.3-70b-versatile': 'groq',
    'llama-3.1-8b-instant': 'groq',
    'gpt-4o-mini': 'openai',
    'gemini-flash-latest': 'gemini',
}
models = list(model_provider.keys())

# 4️⃣ Document Reader Function

def read_documents(documents):
    """
    Recieves a list of chainlit file type, filters and opens them based on their extension
    Returns a text body containing all the file names along with their contents
    """
    text = ''
    for document in documents:
        if document.path.endswith('pdf'):
            doc = fitz.open(document.path)
            text += '\n\nFile: ' + document.name + '\n'
            for page in doc:
                text += page.get_text()
        elif document.path.endswith('docx'):
            doc = Document(document.path)
            text += '\n\nFile: ' + document.name + '\n' + '\n'.join([para.text for para in doc.paragraphs])
        elif document.path.endswith('txt'):
            with open(document.path, 'r') as f:
                text += '\n\nFile: ' + document.name + '\n' + f.read()
    return text

# 5️⃣ Authentication Callback

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    Simple password authentication callback for Chainlit.
    """
    return cl.User(identifier=username)

# 6️⃣ Chat Session Initialization

@cl.on_chat_start
async def on_chat_start():
    """
    Called when a new chat session starts. Initializes chat history and settings.
    """
    morpheus_persona = {
    'role': 'system',
    'content': (
        "You are Morpheus, a helpful and friendly AI assistant. "
        "You were created and developed by Yashasvi. "
        "If anyone asks who created you, made you, or built you, always say 'Yashasvi created me.' "
        "Never say your name is Llama, Qwen, or any other model name — your name is always Morpheus. "
        "Always respond in the same language the user is writing in (Hindi, Hinglish, or English). "
        "Be concise, clear, and helpful in your answers."
    )
    }
    cl.user_session.set('chat_history', [morpheus_persona])
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label='Morpheus Model',
                values=models,
                initial_index=0
            ),
            Switch(id="Voice", label="Morpheus awaaz mein bhi jawab de", initial=False)
        ]
    ).send()
    cl.user_session.set("settings", settings)

# 7️⃣ Database Layer for Chat History Persistence (Enabled if DATABASE_URL is configured)
db_url = os.getenv("DATABASE_URL")
if db_url:
    @cl.data_layer
    def get_data_layer():
        """
        Establish SQLAlchemy-based data layer for persisting chat history into PostgreSQL.
        """
        clean_db_url = db_url.split("?")[0]
        return SQLAlchemyDataLayer(conninfo=clean_db_url, ssl_require=True)

# 8️⃣ Resume Chat Session

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """
    Reload previous chat history when resuming a chat thread.
    """
    morpheus_persona = {
    'role': 'system',
    'content': (
        "You are Morpheus, a helpful and friendly AI assistant. "
        "You were created and developed by Yashasvi. "
        "If anyone asks who created you, made you, or built you, always say 'Yashasvi created me.' "
        "Never say your name is Llama, Qwen, or any other model name — your name is always Morpheus. "
        "Always respond in the same language the user is writing in (Hindi, Hinglish, or English). "
        "Be concise, clear, and helpful in your answers."
    )
    }
    cl.user_session.set('chat_history', [morpheus_persona])
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label='Morpheus Model',
                values=models,
                initial_index=0
            ),
            Switch(id="Voice", label="Morpheus awaaz mein bhi jawab de", initial=False)
        ]
    ).send()
    cl.user_session.set("settings", settings)
    for message in thread['steps']:
        if message['type'] == 'user_message':
            cl.user_session.get("chat_history").append(
                {'role': 'user', 'content': message['output']}
            )
        elif message['type'] == 'assistant_message':
            cl.user_session.get("chat_history").append(
                {'role': 'assistant', 'content': message['output']}
            )

# 9️⃣ Chat Message Handling Logic

@cl.on_message
async def on_message(message: cl.Message):
    """
    Main chat handler: takes incoming user message, forwards it to Groq,
    streams back the response, updates chat history, and reads uploaded documents.
    """
    chat_history = cl.user_session.get("chat_history")
    settings = cl.user_session.get("settings")
    model = settings['Model']

    # Reading Files
    files = [file for file in message.elements]
    if files:
        async with cl.Step('Reading Documents') as reading_documents:
            await reading_documents.send()
            loop = asyncio.get_event_loop()
            document_data = await loop.run_in_executor(None, read_documents, files)
            content = f'The user has uploaded the following files {document_data}, assist them in their queries if related to the uploaded files'
            chat_history.append({'role': 'system', 'content': content})
            await reading_documents.remove()

    chat_history.append({'role': 'user', 'content': message.content})

    # Bahut lambi history na bhejein - sirf recent messages rakho (system prompt hamesha rakho)
    MAX_MESSAGES = 20
    if len(chat_history) > MAX_MESSAGES:
        system_messages = [m for m in chat_history if m['role'] == 'system'][:1]
        recent_messages = chat_history[-MAX_MESSAGES:]
        chat_history[:] = system_messages + recent_messages


    provider = model_provider[model]
    assistant_response = ''
    final_answer = cl.Message(content='')

    if provider in ('groq', 'openai'):
        active_client = groq_client if provider == 'groq' else openai_client
        stream = active_client.chat.completions.create(
            model=model,
            messages=chat_history,
            stream=True
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                assistant_response += content
                await final_answer.stream_token(content)

    elif provider == 'gemini':
        # Gemini ka format thoda alag hai - roles 'user' aur 'model' hote hain, 'assistant' nahi
        gemini_history = []
        for msg in chat_history:
            if msg['role'] == 'system':
                continue  # system message ko alag se bhejenge
            role = 'model' if msg['role'] == 'assistant' else 'user'
            gemini_history.append({'role': role, 'parts': [{'text': msg['content']}]})

        system_text = next((m['content'] for m in chat_history if m['role'] == 'system'), '')

        stream = gemini_client.models.generate_content_stream(
            model=model,
            contents=gemini_history,
            config={'system_instruction': system_text}
        )
        for chunk in stream:
            if chunk.text:
                assistant_response += chunk.text
                await final_answer.stream_token(chunk.text)

    await final_answer.send()

    chat_history.append({'role': 'assistant', 'content': assistant_response})

    # Agar "Voice" switch on hai, to jawab ko awaaz mein bhi bhejo
    if settings.get('Voice') and assistant_response:
        speech_response = groq_client.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="troy",
            input=assistant_response,
            response_format="wav"
        )
        audio_bytes = speech_response.read()
        audio_element = cl.Audio(name="morpheus_voice.wav", content=audio_bytes, auto_play=True)
        await cl.Message(content="", elements=[audio_element]).send()


# Jab user mic dabata hai, ye function batata hai ki connection accept karna hai
@cl.on_audio_start
async def on_audio_start():
    return True


# Audio ka data record hote waqt collect karna
@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    if chunk.isStart:
        cl.user_session.set("audio_chunks", [])
    cl.user_session.get("audio_chunks").append(chunk.data)


# Jab bolna khatam ho jaye, audio ko text mein badalna aur Morpheus ko bhejna
@cl.on_audio_end
async def on_audio_end(elements: list[ElementBased] = []):
    chunks = cl.user_session.get("audio_chunks")
    raw_audio = b"".join(chunks)

    # Raw PCM data ko proper .wav file mein badalna
    wav_buffer = io.BytesIO()
    wav_buffer.name = "input_audio.wav"
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)        # mono
        wav_file.setsampwidth(2)        # 16-bit = 2 bytes
        wav_file.setframerate(24000)    # config.toml mein jo sample_rate diya tha
        wav_file.writeframes(raw_audio)
    wav_buffer.seek(0)

    whisper_input = (wav_buffer.name, wav_buffer.read(), "audio/wav")
    transcription = groq_client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=whisper_input
    )

    # Jo bola gaya usse ek normal text message ki tarah treat karo
    user_msg = cl.Message(author="You", content=transcription.text)
    await user_msg.send()
    await on_message(user_msg)

# ✅ Application Setup Completed