// Top-level App: composes header + welcome/chat + modals + drawer.
// Production mode: no tweaks panel, no bezel frames — fills the viewport
// responsively. The chat is centered in a comfortable column on desktop and
// stretches edge-to-edge on phones.
const { useState: useS, useEffect: useE, useCallback } = React;

const PRODUCT_NAME = "Aside";
const PALETTE = "sage";

const PALETTES = {
  sage: {
    "--bg": "#F4EEE2", "--surface": "#FBF7EE",
    "--ink": "#2A2622", "--ink-soft": "#5C544C", "--ink-mute": "#8A8278",
    "--rule": "#E4DCCC",
    "--sage": "#7A8B6F", "--sage-soft": "#DCE3D2", "--sage-deep": "#5C6E54",
    "--terra": "#B86F52", "--terra-soft": "#F1DDD2", "--terra-bg": "#F7E8DD",
  },
};

function applyPalette(name) {
  const p = PALETTES[name] || PALETTES.sage;
  const root = document.documentElement;
  Object.entries(p).forEach(([k, v]) => root.style.setProperty(k, v));
}

function App() {
  useE(() => { applyPalette(PALETTE); }, []);

  const [messages, setMessages] = useS([]);
  const [thinking, setThinking] = useS(false);
  const [toast, setToast] = useS(null);
  const [drawerOpen, setDrawerOpen] = useS(false);
  const [crisisOpen, setCrisisOpen] = useS(false);
  const [aboutOpen, setAboutOpen] = useS(false);

  const handleSend = useCallback(async (text) => {
    const userMsg = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setThinking(true);

    const reply = await window.MockBackend.sendMessage(text);
    setThinking(false);

    const placeholder = { ...reply, content: "", streaming: true };
    setMessages((m) => [...m, placeholder]);

    const tokens = reply.content.split(/(\s+)/);
    let acc = "";
    for (let i = 0; i < tokens.length; i++) {
      acc += tokens[i];
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { ...placeholder, content: acc, streaming: true };
        return copy;
      });
      await new Promise(r => setTimeout(r, 22 + Math.random() * 28));
    }
    setMessages((m) => {
      const copy = [...m];
      copy[copy.length - 1] = { ...placeholder, content: acc, streaming: false };
      return copy;
    });
  }, []);

  const newConversation = () => {
    if (window.MockBackend?.clearSession) window.MockBackend.clearSession();
    setMessages([]);
    setToast("Starting fresh. Take your time.");
  };

  useE(() => {
    const onKey = (e) => {
      if (e.key !== "Escape") return;
      if (crisisOpen)       setCrisisOpen(false);
      else if (aboutOpen)   setAboutOpen(false);
      else if (drawerOpen)  setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [crisisOpen, aboutOpen, drawerOpen]);

  const empty = messages.length === 0;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "var(--bg)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
      data-screen-label={empty ? "Welcome" : "Chat"}
    >
      <Header
        name={PRODUCT_NAME}
        onMenu={() => setDrawerOpen(true)}
      />

      {empty ? (
        <WelcomeScreen
          name={PRODUCT_NAME}
          onStart={(s) => handleSend(s)}
          onCrisisLink={() => setCrisisOpen(true)}
        />
      ) : (
        <MessageList messages={messages} thinking={thinking} />
      )}

      <MessageInput onSend={handleSend} disabled={thinking} />

      {toast && <Toast onDone={() => setToast(null)}>{toast}</Toast>}

      {drawerOpen && (
        <MenuDrawer
          onClose={() => setDrawerOpen(false)}
          onNew={newConversation}
          onCrisis={() => setCrisisOpen(true)}
          onAbout={() => setAboutOpen(true)}
        />
      )}
      {crisisOpen && (
        <CrisisModal onClose={() => setCrisisOpen(false)} />
      )}
      {aboutOpen && (
        <AboutModal
          name={PRODUCT_NAME}
          onClose={() => setAboutOpen(false)}
          onCrisisLink={() => {
            setAboutOpen(false);
            setCrisisOpen(true);
          }}
        />
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
