// Modals: Crisis resources, About; plus the slide-in MenuDrawer
const { useEffect: useEffect2 } = React;

function Overlay({ children, onDismiss }) {
  return (
    <div
      role="presentation"
      onClick={(e) => { if (e.target === e.currentTarget) onDismiss && onDismiss(); }}
      style={{
        position: "absolute",
        inset: 0,
        background: "rgba(31, 28, 25, 0.42)",
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        zIndex: 60,
        animation: "overlay-in 0.18s ease both",
        padding: 12,
      }}
    >
      {children}
    </div>
  );
}

function Sheet({ children, ariaLabel }) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      className="scroll-area"
      style={{
        width: "100%",
        maxWidth: 480,
        maxHeight: "92%",
        background: "var(--bg)",
        borderRadius: 22,
        padding: "26px 24px 22px",
        animation: "sheet-in 0.24s cubic-bezier(0.2, 0.7, 0.3, 1) both",
        overflowY: "auto",
        boxShadow: "0 -1px 0 rgba(255,255,255,0.4) inset",
      }}
    >
      {children}
    </div>
  );
}

function CrisisModal({ onClose }) {
  return (
    <Overlay onDismiss={onClose}>
      <Sheet ariaLabel="Crisis resources">
        <h2
          style={{
            fontFamily: "var(--serif)",
            fontWeight: 500,
            fontSize: 26,
            lineHeight: 1.2,
            letterSpacing: "-0.01em",
            margin: "0 0 8px",
            color: "var(--ink)",
            textWrap: "pretty",
          }}
        >
          You're not alone — <em style={{ fontStyle: "italic", color: "var(--terra)" }}>please reach out.</em>
        </h2>
        <p
          style={{
            fontFamily: "var(--serif)",
            fontSize: 16,
            color: "var(--ink-soft)",
            margin: "0 0 22px",
            textWrap: "pretty",
          }}
        >
          These services are free, confidential, and available right now. Tap any number to call or text from this device.
        </p>

        <ul style={{ listStyle: "none", padding: 0, margin: "0 0 22px", display: "grid", gap: 10 }}>
          <ResourceRow
            name="988 Suicide & Crisis Lifeline"
            blurb="Talk or text with a trained counselor, any hour."
            actions={[
              { label: "Call 988", href: "tel:988" },
              { label: "Text 988", href: "sms:988" },
            ]}
          />
          <ResourceRow
            name="SAMHSA National Helpline"
            blurb="Treatment referrals for substance use and mental health."
            actions={[{ label: "Call 1-800-662-4357", href: "tel:18006624357" }]}
          />
          <ResourceRow
            name="Crisis Text Line"
            blurb="Text-based support with a trained counselor."
            actions={[{ label: "Text HOME to 741741", href: "sms:741741?body=HOME" }]}
          />
        </ul>

        <button
          onClick={onClose}
          style={{
            width: "100%",
            padding: "12px 16px",
            border: "1px solid var(--ink)",
            background: "transparent",
            color: "var(--ink)",
            borderRadius: 999,
            fontSize: 15,
            fontFamily: "var(--sans)",
            cursor: "pointer",
          }}
        >
          Close
        </button>
      </Sheet>
    </Overlay>
  );
}

function ResourceRow({ name, blurb, actions }) {
  return (
    <li
      style={{
        padding: "14px 14px 12px",
        background: "var(--surface)",
        border: "1px solid var(--rule)",
        borderRadius: 14,
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 500, color: "var(--ink)", marginBottom: 2 }}>{name}</div>
      <div style={{ fontSize: 13, color: "var(--ink-mute)", marginBottom: 10, lineHeight: 1.4 }}>{blurb}</div>
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
              padding: "6px 12px",
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

function AboutModal({ name, onClose, onCrisisLink }) {
  return (
    <Overlay onDismiss={onClose}>
      <Sheet ariaLabel="About">
        <div
          style={{
            fontFamily: "var(--mono)",
            fontSize: 10,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "var(--ink-mute)",
            marginBottom: 8,
          }}
        >
          About {name}
        </div>
        <h2
          style={{
            fontFamily: "var(--serif)",
            fontWeight: 500,
            fontSize: 26,
            lineHeight: 1.2,
            letterSpacing: "-0.01em",
            margin: "0 0 18px",
            color: "var(--ink)",
            textWrap: "pretty",
          }}
        >
          A quiet place to think out loud.
        </h2>

        <div
          style={{
            display: "grid", gap: 14,
            fontFamily: "var(--serif)", fontSize: 16, lineHeight: 1.55,
            color: "var(--ink-soft)", textWrap: "pretty",
          }}
        >
          <p style={{ margin: 0 }}>
            <strong style={{ color: "var(--ink)", fontWeight: 600 }}>What this is.</strong>{" "}
            A research prototype offering a listening space, grounded in Motivational Interviewing — a way of talking that meets you where you are, without telling you what to do.
          </p>
          <p style={{ margin: 0 }}>
            <strong style={{ color: "var(--ink)", fontWeight: 600 }}>What this isn't.</strong>{" "}
            Not therapy. Not a substitute for a clinician. Not a crisis service. If anything you're carrying needs that level of care, please reach out to one of those services instead.
          </p>
          <p style={{ margin: 0 }}>
            <strong style={{ color: "var(--ink)", fontWeight: 600 }}>Privacy.</strong>{" "}
            Conversations aren't shared, sold, or used to identify you. They're held only as long as needed to support the conversation itself.
          </p>
        </div>

        <div
          style={{
            marginTop: 22,
            paddingTop: 16,
            borderTop: "1px solid var(--rule)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 12,
          }}
        >
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
              fontSize: 14,
              fontFamily: "var(--sans)",
            }}
          >
            Crisis resources →
          </button>
          <button
            onClick={onClose}
            style={{
              padding: "9px 18px",
              border: "1px solid var(--ink)",
              background: "transparent",
              color: "var(--ink)",
              borderRadius: 999,
              fontSize: 14,
              fontFamily: "var(--sans)",
              cursor: "pointer",
            }}
          >
            Close
          </button>
        </div>
      </Sheet>
    </Overlay>
  );
}

function MenuDrawer({ onClose, onNew, onCrisis, onAbout }) {
  const items = [
    { icon: <Icon.Plus />,    label: "New conversation",  onClick: onNew },
    { icon: <Icon.Heart />,   label: "Crisis resources",  onClick: onCrisis, accent: true },
    { icon: <Icon.Info />,    label: "About",             onClick: onAbout },
  ];
  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: "absolute", inset: 0, zIndex: 55,
        background: "rgba(31,28,25,0.32)",
        animation: "overlay-in 0.16s ease both",
      }}
    >
      <aside
        role="dialog"
        aria-label="Menu"
        style={{
          position: "absolute",
          top: 0, right: 0, bottom: 0,
          width: "min(280px, 80%)",
          background: "var(--bg)",
          borderLeft: "1px solid var(--rule)",
          padding: "16px 18px",
          animation: "drawer-in 0.22s cubic-bezier(0.2,0.7,0.3,1) both",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 18 }}>
          <button
            onClick={onClose}
            aria-label="Close menu"
            style={{
              background: "transparent", border: "none", padding: 8, margin: -8,
              cursor: "pointer", color: "var(--ink-soft)",
            }}
          >
            <Icon.Close />
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {items.map((it) => (
            <button
              key={it.label}
              onClick={() => { it.onClick(); onClose(); }}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "12px 12px",
                background: "transparent",
                border: "none",
                borderRadius: 12,
                color: it.accent ? "var(--terra)" : "var(--ink)",
                fontSize: 15,
                fontFamily: "var(--sans)",
                cursor: "pointer",
                textAlign: "left",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {it.icon}
              <span>{it.label}</span>
            </button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        <p
          style={{
            fontFamily: "var(--mono)",
            fontSize: 10,
            letterSpacing: "0.12em",
            color: "var(--ink-mute)",
            textTransform: "uppercase",
            margin: 0,
          }}
        >
          v0.1 — research prototype
        </p>
      </aside>
    </div>
  );
}

Object.assign(window, { CrisisModal, AboutModal, MenuDrawer });
