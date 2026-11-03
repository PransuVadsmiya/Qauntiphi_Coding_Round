import { useEffect, useRef, useState } from "react";
import { api } from "../api";

const SUGGESTIONS = [
  "What are this developer's strongest skills?",
  "Which project best shows backend experience?",
  "Has this developer worked with machine learning?",
  "How active have they been recently?",
];

/** Extra feature 1: floating "Ask my Portfolio" chatbot. */
export default function ChatPanel({ login }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  // Effects must return nothing (or a cleanup function), so use block bodies.
  useEffect(() => {
    setMessages([]);
  }, [login]);
  useEffect(() => {
    // Scroll only the chat box, never the page behind it.
    const body = endRef.current?.parentElement;
    if (open && body) body.scrollTop = body.scrollHeight;
  }, [messages, busy, open]);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const send = async (text) => {
    const msg = text.trim();
    if (!msg || busy) return;
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.chat(login, msg, history);
      setMessages((m) => [...m, { role: "assistant", content: res.reply, source: res.source }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `⚠️ ${e.message}`, source: "error" }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} aria-label="Ask my Portfolio">
          💬 Ask my Portfolio
        </button>
      )}
      {open && (
        <div className="chat-window">
          <div className="chat-head">
            <div>
              <strong>Ask about @{login}</strong>
              <span className="muted small">Answers come from the cached GitHub data</span>
            </div>
            <button className="ghost icon chat-close" onClick={() => setOpen(false)} aria-label="Close chat" title="Close">
              ✕
            </button>
          </div>
          <div className="chat-body">
            {messages.length === 0 && (
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="ghost" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>
                {m.content}
                {m.source && m.source !== "error" && (
                  <span className="source">{m.source === "llm" ? "AI" : "rule-based"}</span>
                )}
              </div>
            ))}
            {busy && <div className="bubble assistant typing">Thinking…</div>}
            <div ref={endRef} />
          </div>
          <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(input); }}>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Has this developer used React?" />
            <button disabled={busy || !input.trim()}>Send</button>
          </form>
        </div>
      )}
    </>
  );
}
