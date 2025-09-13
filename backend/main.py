from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import requests

# === Database Setup ===
DB = "lab_chatbot.db"

app = FastAPI(title="Medical Lab Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        test TEXT,
        date TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        name TEXT PRIMARY KEY,
        bookings INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# === Sample Tests ===
TESTS = [
    {"id": "blood", "name": "Complete Blood Count (CBC)", "price": 500, "prep": "Fasting 8 hours"},
    {"id": "thyroid", "name": "Thyroid Profile", "price": 800, "prep": "No fasting required"},
    {"id": "diabetes", "name": "Fasting Blood Sugar", "price": 600, "prep": "Fasting 10 hours"}
]

# === Models ===
class ChatRequest(BaseModel):
    user: str
    message: str

class BookingRequest(BaseModel):
    name: str
    phone: str
    test_id: str
    date: str

# === Gemini Integration ===
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def ask_gemini(user_message, user_name):
    """
    Send message to Gemini 1.5 Flash and get the reply.
    """
    if not GEMINI_KEY:
        return "⚠️ Gemini API key not set. Please configure GEMINI_API_KEY."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateText?key={GEMINI_KEY}"
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are HealthPlus Medical Lab chatbot. "
                        f"User name: {user_name or 'Customer'}. "
                        f"User message: {user_message}. "
                        f"Reply in a friendly tone and help with information on lab tests, appointment bookings, and loyalty offers. "
                        f"If user asks about test prices, use: {TESTS}"
            }]
        }]
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        return data["candidates"][0]["co]()
