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
    Logs the raw JSON for debugging.
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
        print("Gemini raw response:", data)  # <-- Debug: raw response
        if "candidates" not in data:
            return f"Gemini API error: {data}"
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error contacting Gemini: {str(e)}"

# === Endpoints ===

@app.get("/")
def root():
    return {"status": "ok", "message": "Medical Lab Chatbot API is running!"}

@app.get("/api/tests")
def get_tests():
    return {"tests": TESTS}

@app.post("/api/book")
def book(req: BookingRequest):
    test = next((t for t in TESTS if t["id"] == req.test_id), None)
    if not test:
        raise HTTPException(status_code=400, detail="Invalid test id")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO bookings (name, phone, test, date) VALUES (?, ?, ?, ?)",
              (req.name, req.phone, test["name"], req.date))
    c.execute("INSERT OR IGNORE INTO customers (name, bookings) VALUES (?, 0)", (req.name,))
    c.execute("UPDATE customers SET bookings = bookings + 1 WHERE name = ?", (req.name,))
    conn.commit()
    c.execute("SELECT bookings FROM customers WHERE name = ?", (req.name,))
    bookings = c.fetchone()[0]
    conn.close()

    offer = None
    if bookings >= 5:
        offer = "🎉 Congrats! You get 1 free test after 5 bookings."
    elif bookings >= 2:
        offer = "🎉 You have unlocked 10% off on your next test."

    return {"status": "ok", "booking_for": req.name, "test": test, "date": req.date, "offer": offer}

@app.post("/api/chat")
def chat(req: ChatRequest):
    reply = ask_gemini(req.message, req.user)
    return {"reply": reply}

@app.get("/api/offers")
def get_offers(name: Optional[str] = None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    offer = None
    bookings = 0
    if name:
        c.execute("SELECT bookings FROM customers WHERE name = ?", (name,))
        r = c.fetchone()
        if r:
            bookings = r[0]
    conn.close()

    if bookings >= 5:
        offer = "1 free test after 5 bookings"
    elif bookings >= 2:
        offer = "10% off next test"
    else:
        offer = "No active offers. Book more to unlock discounts!"

    return {"name": name, "bookings": bookings, "offer": offer}

# === Uvicorn Run (for local dev) ===
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
