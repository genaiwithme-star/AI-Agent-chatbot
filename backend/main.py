import os, requests

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

def ask_gemini(user_message, user_name):
    if not GEMINI_KEY:
        return "Gemini API key not set. Please configure GEMINI_API_KEY."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateText?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"User: {user_name}\\nMessage: {user_message}\\nReply as a friendly medical lab chatbot, give helpful information on tests, bookings and offers."}]}]
    }
    r = requests.post(url, json=payload, timeout=15)
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return "Error from Gemini: " + str(data)
