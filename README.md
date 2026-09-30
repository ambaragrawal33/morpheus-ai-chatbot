# 🟢 Morpheus AI

> **Enter the Matrix.** A high-performance, multimodal conversational AI assistant built with Chainlit, Groq, OpenAI, and Google Gemini.

---

## ⚡ Features

- **Multi-Model Inference**: Switch seamlessly between Groq (Llama 3.3 70B, Llama 3.1 8B), OpenAI (GPT-4o-mini), and Google Gemini (Gemini Flash).
- **Matrix Movie Aesthetic**: Black and phosphor-green digital terminal styling with custom CSS, neon glowing controls, and CRT scanlines.
- **Document Intelligence**: Upload and analyze `.pdf`, `.docx`, and `.txt` files directly in conversation.
- **Two-Way Voice**:
  - **Speech-to-Text (STT)**: User voice recorded and transcribed with Groq Whisper (`whisper-large-v3-turbo`).
  - **Text-to-Speech (TTS)**: Voice responses powered by Canopy Labs Orpheus (`canopylabs/orpheus-v1-english`).
- **Persistent Chat History**: PostgreSQL database integration via SQLAlchemy and `asyncpg`.
- **Multilingual Support**: Fluent in English, Hindi, and Hinglish.

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
```

### 3. Run Application
```bash
chainlit run morpheus_ai.py -w
```
*(Alternatively, `chainlit run app.py -w` is also supported)*

---

## 🐳 Docker Deployment
```bash
docker build -t morpheus-ai .
docker run -p 7860:7860 -e PORT=7860 --env-file .env morpheus-ai
```
