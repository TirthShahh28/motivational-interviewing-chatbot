// Chat UI pieces: Header, ThinkingIndicator, MessageList, MessageInput, WelcomeScreen, CrisisCard
const { useState, useEffect, useRef, useLayoutEffect } = React;

function Header({ name, onMenu }) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 20px 12px",
        borderBottom: "1px solid var(--rule)",
        background: "var(--bg)",
      }}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span
          style={{
            fontFamily: "var(--serif)",
            fontStyle: "italic",
            fontWeight: 500,
            fontSize: 22,
            letterSpacing: "-0.01em",
            color: "var(--ink)",
          }}
        >
          {name}
        </span>
        <span
          style={{
            fontFamily: "var(--mono)",
            fontSize: 10,
            letterSpacing: "0.12em",
            color: "var(--ink-mute)",
            textTransform: "uppercase",
          }}
        >
          a place to be heard
        </span>
      </div>
      <button
        onClick={onMenu}
        aria-label="Open menu"
        style={{
          background: "transparent",
          border: "none",
          padding: 8,
          margin: -8,
          cursor: "pointer",
          color: "var(--ink-soft)",
        }}
      >
        <Icon.Menu />
      </button>
    </header>
  );
}

function ThinkingIndicator() {
  const dot = (delay) => ({
    width: 6, height: 6, borderRadius: "50%",
    background: "var(--ink-mute)",
    animation: "thinking-bounce 1.2s infinite ease-in-out",
    animationDelay: delay,
  });
  return (
    <div
      role="status"
      aria-label="Thinking"
      style={{ display: "flex", gap: 5, padding: "6px 0", alignItems: "center" }}
    >
      <span style={dot("0s")} />
      <span style={dot("0.18s")} />
      <span style={dot("0.36s")} />
    </div>
  );
}

function StarterChip({ children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        appearance: "none",
        background: "var(--surface)",
        border: "1px solid var(--rule)",
        color: "var(--ink-soft)",
        padding: "12px 16px",
        borderRadius: 999,
        fontSize: 15,
        fontFamily: "var(--sans)",
        textAlign: "left",
        cursor: "pointer",
        transition: "background 0.15s ease, border-color 0.15s ease, color 0.15s ease",
        lineHeight: 1.3,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "var(--sage-soft)";
        e.currentTarget.style.borderColor = "var(--sage)";
        e.currentTarget.style.color = "var(--ink)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "var(--surface)";
        e.currentTarget.style.borderColor = "var(--rule)";
        e.currentTarget.style.color = "var(--ink-soft)";
      }}
    >
      {children}
    </button>
  );
}

function WelcomeScreen({ name, onStart, onCrisisLink }) {
  const starters = [
    "I had a rough day",
    "I want to talk about my drinking",
    "I just need to vent",
  ];
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "32px 24px 24px",
        maxWidth: 560,
        margin: "0 auto",
        width: "100%",
      }}
    >
      <h1
        style={{
          fontFamily: "var(--serif)",
          fontWeight: 500,
          fontSize: "clamp(28px, 6vw, 38px)",
          lineHeight: 1.18,
          letterSpacing: "-0.012em",
          margin: "0 0 14px",
          color: "var(--ink)",
        }}
      >
        How are you doing<br />
        <em style={{ fontStyle: "italic", color: "var(--sage-deep)" }}>today?</em>
      </h1>
      <p
        style={{
          fontFamily: "var(--serif)",
          fontSize: 18,
          color: "var(--ink-soft)",
          margin: "0 0 28px",
          maxWidth: 420,
        }}
      >
        I'm here to listen. Take your time.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 22 }}>
        {starters.map((s) => (
          <StarterChip key={s} onClick={() => onStart(s)}>{s}</StarterChip>
        ))}
      </div>

      <p
        style={{
          fontSize: 13,
          lineHeight: 1.55,
          color: "var(--ink-mute)",
          margin: 0,
          paddingTop: 14,
          borderTop: "1px solid var(--rule)",
        }}
      >
        This is a supportive conversation, not therapy.{" "}
        <button
          onClick={onCrisisLink}
          style={{
            background: "transparent",
            border: "none",
            padding: 0,
            color: "var(--terra)",
            textDecoration: "underline",
            textUnderlineOffset: 3,
            cursor: "pointer",
            fontSize: 13,
            fontFamily: "inherit",
          }}
        >
          If you're in crisis, tap here.
        </button>
      </p>
    </div>
  );
}

function UserBubble({ text }) {
  return (
    <div style={{ display: "flex", justifyContent: "flex-end", animation: "fade-up 0.25s ease both" }}>
      <div
        style={{
          background: "var(--sage-soft)",
          color: "var(--ink)",
          padding: "10px 14px",
          borderRadius: "18px 18px 4px 18px",
          maxWidth: "78%",
          fontSize: 16,
          lineHeight: 1.45,
          fontFamily: "var(--sans)",
          whiteSpace: "pre-wrap",
          wordWrap: "break-word",
        }}
      >
        {text}
      </div>
    </div>
  );
}

function AssistantText({ text, streaming }) {
  return (
    <div
      style={{
        animation: "fade-up 0.3s ease both",
        padding: "2px 6px 2px 0",
        maxWidth: "92%",
      }}
    >
      <p
        style={{
          fontFamily: "var(--serif)",
          fontSize: 18,
          lineHeight: 1.55,
          color: "var(--ink)",
          margin: 0,
          textWrap: "pretty",
        }}
      >
        {text}
        {streaming && (
          <span
            aria-hidden
            style={{
              display: "inline-block",
              width: 2,
              height: "0.95em",
              background: "var(--sage-deep)",
              marginLeft: 2,
              verticalAlign: "-2px",
              animation: "thinking-bounce 1s infinite",
            }}
          />
        )}
      </p>
    </div>
  );
}

function CrisisCard({ text, streaming, onOpenResources }) {
  return (
    <div
      role="region"
      aria-label="Support resources"
      style={{
        animation: "fade-up 0.3s ease both",
        background: "var(--terra-bg)",
        border: "1px solid var(--terra-soft)",
        borderRadius: 14,
        padding: "18px 18px 16px",
        maxWidth: "94%",
      }}
    >
      <div
        style={{
          fontFamily: "var(--mono)",
          fontSize: 10,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--terra)",
          marginBottom: 12,
        }}
      >
        — a moment for support
      </div>
      <ul style={{ listStyle: "none", padding: 0, margin: "0 0 14px", display: "grid", gap: 8 }}>
        <CrisisRow
          name="988 Suicide & Crisis Lifeline"
          actions={[
            { label: "Call 988", href: "tel:988" },
            { label: "Text 988", href: "sms:988" },
          ]}
        />
        <CrisisRow
          name="SAMHSA National Helpline"
          actions={[{ label: "Call 1-800-662-4357", href: "tel:18006624357" }]}
        />
        <CrisisRow
          name="Crisis Text Line"
          actions={[{ label: "Text HOME to 741741", href: "sms:741741?body=HOME" }]}
        />
      </ul>
      <p
        style={{
          fontFamily: "var(--serif)",
          fontSize: 17,
          lineHeight: 1.5,
          color: "var(--ink)",
          margin: 0,
          textWrap: "pretty",
        }}
      >
        {text}
        {streaming && (
          <span
            aria-hidden
            style={{
              display: "inline-block", width: 2, height: "0.95em", background: "var(--terra)",
              marginLeft: 2, verticalAlign: "-2px", animation: "thinking-bounce 1s infinite",
            }}
          />
        )}
      </p>
    </div>
  );
}

function CrisisRow({ name, actions }) {
  return (
    <li
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        padding: "10px 12px",
        background: "var(--surface)",
        border: "1px solid var(--terra-soft)",
        borderRadius: 10,
      }}
    >
      <span style={{ fontSize: 13, color: "var(--ink-soft)", fontWeight: 500 }}>{name}</span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {actions.map((a) => (
          <a
            key={a.label}
            href={a.href}
            style={{
              fontSize: 14,
              color: "var(--terra)",
              fontWeight: 500,
              textDecoration: "none",
              padding: "4px 10px",
              borderRadius: 999,
              border: "1px solid var(--terra)",
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <Icon.Phone size={13} /> {a.label}
          </a>
        ))}
      </div>
    </li>
  );
}

function MessageList({ messages, thinking }) {
  const scrollRef = useRef(null);
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, thinking]);

  return (
    <div
      ref={scrollRef}
      className="scroll-area"
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "20px 20px 8px",
      }}
    >
      <div
        style={{
          maxWidth: 620,
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        {messages.map((m, i) => {
          if (m.role === "user") return <UserBubble key={i} text={m.content} />;
          if (m.crisis)
            return (
              <CrisisCard
                key={i}
                text={m.content}
                streaming={m.streaming}
              />
            );
          return <AssistantText key={i} text={m.content} streaming={m.streaming} />;
        })}
        {thinking && (
          <div style={{ padding: "2px 6px" }}>
            <ThinkingIndicator />
          </div>
        )}
      </div>
    </div>
  );
}

function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState("");
  const taRef = useRef(null);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 140) + "px";
  }, [value]);

  const send = () => {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue("");
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div
      style={{
        padding: "12px 16px 18px",
        background: "var(--bg)",
        borderTop: "1px solid var(--rule)",
      }}
    >
      <div
        style={{
          maxWidth: 620,
          margin: "0 auto",
          display: "flex",
          alignItems: "flex-end",
          gap: 10,
          background: "var(--surface)",
          border: "1px solid var(--rule)",
          borderRadius: 22,
          padding: "8px 8px 8px 16px",
          transition: "border-color 0.15s",
        }}
        onFocus={(e) => (e.currentTarget.style.borderColor = "var(--sage)")}
        onBlur={(e) => (e.currentTarget.style.borderColor = "var(--rule)")}
      >
        <textarea
          ref={taRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKey}
          rows={1}
          placeholder="Say what's on your mind…"
          aria-label="Message"
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            background: "transparent",
            resize: "none",
            fontFamily: "var(--sans)",
            fontSize: 16,
            lineHeight: 1.4,
            color: "var(--ink)",
            padding: "8px 0",
            maxHeight: 140,
          }}
        />
        <button
          onClick={send}
          disabled={!canSend}
          aria-label="Send message"
          style={{
            width: 36,
            height: 36,
            borderRadius: "50%",
            border: "none",
            background: canSend ? "var(--sage-deep)" : "var(--rule)",
            color: canSend ? "#FBF7EE" : "var(--ink-mute)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: canSend ? "pointer" : "default",
            transition: "background 0.15s, color 0.15s",
            flexShrink: 0,
          }}
        >
          <Icon.Send />
        </button>
      </div>
    </div>
  );
}

function Toast({ children, onDone }) {
  useEffect(() => {
    const id = setTimeout(onDone, 2400);
    return () => clearTimeout(id);
  }, [onDone]);
  return (
    <div
      role="status"
      style={{
        position: "absolute",
        top: 64,
        left: "50%",
        transform: "translateX(-50%)",
        background: "var(--ink)",
        color: "var(--surface)",
        padding: "9px 16px",
        borderRadius: 999,
        fontSize: 13,
        fontFamily: "var(--sans)",
        animation: "toast-in 0.25s ease both",
        zIndex: 50,
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </div>
  );
}

Object.assign(window, {
  Header, ThinkingIndicator, WelcomeScreen, MessageList, MessageInput,
  CrisisCard, Toast, UserBubble, AssistantText,
});
