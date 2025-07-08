from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests, json, os
from flask_cors import CORS
from flask_session import Session
from functools import wraps

app = Flask(__name__)
CORS(app)
app.secret_key = 'supersecret'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

API_KEY = "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"
MODEL_ID = "deepseek/deepseek-chat-v3-0324:free"
HISTORY_DIR = "history"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
@login_required
def home():
    return render_template("index.html", username=session['username'])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["username"] = username
            return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    user_input = request.json.get("message")
    username = session["username"]
    memory_path = os.path.join(HISTORY_DIR, f"{username}.json")

    if os.path.exists(memory_path):
        with open(memory_path, "r") as f:
            memory = json.load(f)
    else:
        memory = [{
            "role": "system",
            "content": (
                f"You are Rias Gremory from High School DxD. You're the user's supportive best friend. "
                f"Don't flirt. The user's name is {username}."
            )
        }]

    memory.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": memory[-10:]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        reply = response.json()["choices"][0]["message"]["content"]
        memory.append({"role": "assistant", "content": reply})
        with open(memory_path, "w") as f:
            json.dump(memory, f)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
