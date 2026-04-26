// Real backend client for Aside.
// Talks to FastAPI at /api/chat (same origin — see backend_server.py).
// Returns the same shape the UI already expects: { role, content, crisis?, crisisPayload? }

const API_BASE = ""; // same origin
let _sessionId = null;

function getSessionId() { return _sessionId; }
function clearSession() { _sessionId = null; }

async function sendMessage(text) {
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        session_id: _sessionId,
      }),
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      console.error("chat API error", res.status, detail);
      return {
        role: "assistant",
        content: "I'm having trouble connecting right now. Could you try again in a moment?",
      };
    }

    const data = await res.json();
    if (data.session_id) _sessionId = data.session_id;

    return {
      role: data.role || "assistant",
      content: data.content,
      crisis: !!data.crisis,
      crisisPayload: data.crisisPayload || undefined,
    };
  } catch (err) {
    console.error("network error", err);
    return {
      role: "assistant",
      content: "I lost the connection for a second. Can you try again?",
    };
  }
}

window.MockBackend = { sendMessage, getSessionId, clearSession };
