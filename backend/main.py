from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import requests

DB = "lab_chatbot.db"

app = FastAPI(title="Medical Lab Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Database Setup ===
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

# === Tests ===
TESTS = [
    {"id": "blood", "name": "Complete Blood Count (CBC)", "price": 500, "prep": "Fasting 8 hours"},
    {"id": "thyroid", "name": "Thyroid Profile", "price": 800, "prep": "No fasting required"},
    {"id": "diabetes", "name": "Fasting Blood Sugar", "price": 600, "prep": "Fasting 10 hours"}
]

@app.get("/api/tests")
def get_tests():
    return {"tests": TESTS}

@app.get("/api/labinfo")
def lab_info():
    return {
        "name": "HealthPlus Medical Lab",
        "address": "123 Main Road, New Delhi, India",
        "google_map": "https://maps.google.com/?q=HealthPlus+Medical+Lab+New+Delhi"
    }

# === Models ===
class ChatRequest(BaseModel):
    user: str
    message: str
    lang: str = "en"

class BookingRequest(BaseModel):
    name: str
    phone: str
    test_id: str
    date: str

# === Gemini Integration ===
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def ask_gemini(user_message, user_name, lang="en"):
    if not GEMINI_KEY:
        return "⚠️ Gemini API key not set."

    language_instruction = "Reply in Hindi." if lang == "hi" else "Reply in English."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are HealthPlus Medical Lab chatbot. "
                        f"User name: {user_name or 'Customer'}. "
                        f"User message: {user_message}. "
                        f"Use a friendly tone and help with lab tests, appointment bookings, and loyalty offers. "
                        f"If user asks about test prices, use: {TESTS}. "
                        f"{language_instruction}"
            }]
        }]
    }

    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini API error:", e, data if 'data' in locals() else '')
        return "Sorry, Gemini API error."

@app.post("/api/chat")
def chat(req: ChatRequest):
    reply = ask_gemini(req.message, req.user, req.lang)
    return {"reply": reply}

@app.post("/api/book")
def book(req: BookingRequest):
    test = next((t for t in TESTS if t["id"] == req.test_id), None)
    if not test:
        return {"error": "Invalid test_id"}

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO bookings (name, phone, test, date) VALUES (?,?,?,?)",
              (req.name, req.phone, req.test_id, req.date))
    conn.commit()

    # loyalty offers
    c.execute("SELECT bookings FROM customers WHERE name=?",(req.name,))
    row = c.fetchone()
    offer = None
    if row:
        bookings_count = row[0] + 1
        c.execute("UPDATE customers SET bookings=? WHERE name=?",(bookings_count,req.name))
    else:
        bookings_count = 1
        c.execute("INSERT INTO customers (name,bookings) VALUES (?,?)",(req.name,1))
    conn.commit()
    conn.close()

    if bookings_count >= 3:
        offer = "Congrats! You earned 10% off on your next test."

    return {
        "status": "ok",
        "test": test,
        "booking_for": req.name,
        "date": req.date,
        "offer": offer
    }
