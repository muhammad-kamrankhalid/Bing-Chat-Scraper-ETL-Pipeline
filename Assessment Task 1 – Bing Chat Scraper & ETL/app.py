from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Inline HTML for simplicity; includes a minimal "chat UI"
CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Local Chat Demo</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }
    .chat { max-width: 720px; margin: 0 auto; border: 1px solid #ddd; border-radius: 12px; padding: 16px; }
    .row { display: flex; gap: 8px; margin-top: 12px; }
    textarea { flex: 1; height: 60px; padding: 8px; }
    button { padding: 10px 16px; cursor: pointer; }
    .messages { margin-top: 16px; }
    .msg { padding: 10px 12px; border-radius: 10px; margin-bottom: 10px; }
    .user { background: #eef6ff; }
    .bot  { background: #f5f5f5; }
    .meta { font-size: 12px; color: #777; margin-top: 2px; }
  </style>
</head>
<body>
  <h2>Local Chat Demo</h2>
  <div class="chat">
    <div id="messages" class="messages" data-testid="chat-messages"></div>
    <div class="row">
      <textarea id="chat-input" placeholder="Type your message..." data-testid="chat-input"></textarea>
      <button id="send-btn" data-testid="send-btn">Send</button>
    </div>
  </div>

  <script>
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const messages = document.getElementById('messages');

    function appendMessage(role, text) {
      const div = document.createElement('div');
      div.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
      div.setAttribute('data-testid', 'chat-message');
      const p = document.createElement('div');
      p.setAttribute('data-testid', 'chat-message-content');
      p.textContent = text;
      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = new Date().toLocaleString();
      div.appendChild(p);
      div.appendChild(meta);
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;
      appendMessage('user', text);
      input.value = '';
      sendBtn.disabled = true;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query: text})
        });
        const data = await res.json();
        appendMessage('bot', data.response);
      } catch (e) {
        appendMessage('bot', 'Error: ' + e.toString());
      } finally {
        sendBtn.disabled = false;
      }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  </script>
</body>
</html>
"""

@app.route("/")
def root():
    return "<p>Go to <a href='/chat'>/chat</a></p>"

@app.route("/chat")
def chat():
    return render_template_string(CHAT_HTML)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    # Simple "bot": echo + a tiny transformation to mimic processing
    response = f"[EchoBot] You said: {query} | length={len(query)} | time={datetime.utcnow().isoformat()}Z"
    return jsonify({"response": response})

if __name__ == "__main__":
    # Run local app
    app.run(host="127.0.0.1", port=5000, debug=False)
