from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import Optional

DB = "lab_chatbot.db"

app = FastAPI(title="Medical Lab Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple DB init
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

# Sample tests
TESTS = [
    {"id": "blood", "name": "Complete Blood Count (CBC)", "price": 500, "prep": "Fasting 8 hours"},
    {"id": "thyroid", "name": "Thyroid Profile", "price": 800, "prep": "No fasting required"},
    {"id": "diabetes", "name": "Fasting Blood Sugar", "price": 600, "prep": "Fasting 10 hours"}
]

class ChatRequest(BaseModel):
    user: str
    message: str

class BookingRequest(BaseModel):
    name: str
    phone: str
    test_id: str
    date: str

@app.get("/api/tests")
def get_tests():
    return {"tests": TESTS}

@app.post("/api/book")
def book(req: BookingRequest):
    # validate test
    test = next((t for t in TESTS if t["id"] == req.test_id), None)
    if not test:
        raise HTTPException(status_code=400, detail="Invalid test id")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO bookings (name, phone, test, date) VALUES (?, ?, ?, ?)",
              (req.name, req.phone, test["name"], req.date))
    # increment customer bookings
    c.execute("INSERT OR IGNORE INTO customers (name, bookings) VALUES (?, 0)", (req.name,))
    c.execute("UPDATE customers SET bookings = bookings + 1 WHERE name = ?", (req.name,))
    conn.commit()
    # check offers
    c.execute("SELECT bookings FROM customers WHERE name = ?", (req.name,))
    bookings = c.fetchone()[0]
    conn.close()
    offer = None
    if bookings >= 5:
        offer = "Congrats! You get 1 free test after 5 bookings."
    elif bookings >= 2:
        offer = "You have unlocked 10% off on your next test."
    return {"status": "ok", "booking_for": req.name, "test": test, "date": req.date, "offer": offer}

@app.post("/api/chat")
def chat(req: ChatRequest):
    # Very simple rule-based responder to simulate AI
    msg = req.message.lower()
    if "price" in msg or "cost" in msg:
        suggestions = [f"{t['name']}: ₹{t['price']}" for t in TESTS]
        return {"reply": "Here are some test prices:\n" + "\n".join(suggestions)}
    if "book" in msg or "appointment" in msg:
        return {"reply": "To book please provide your name, phone, test id (e.g. 'blood'), and preferred date (YYYY-MM-DD). Or use the booking form."}
    if "offer" in msg or "discount" in msg:
        return {"reply": "We offer loyalty discounts: 10% off after 2 bookings and 1 free test after 5 bookings."}
    if "hello" in msg or "hi" in msg:
        return {"reply": f"Hello {req.user or 'there'}! I can help with test info, booking appointments, and offers."}
    # default
    return {"reply": "Sorry I didn't understand. Ask about 'tests', 'prices', 'book appointment' or 'offers'."}

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
    if bookings >=5:
        offer = "1 free test after 5 bookings"
    elif bookings >=2:
        offer = "10% off next test"
    else:
        offer = "No active offers. Book more to unlock discounts!"
    return {"name": name, "bookings": bookings, "offer": offer}

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
