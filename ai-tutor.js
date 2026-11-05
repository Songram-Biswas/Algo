/**
 * AlgoHub AI Tutor — reusable, framework-free side panel.
 *
 * Usage (inside an existing <script type="module">):
 *
 *   import { initAITutor } from './ai-tutor.js';
 *   initAITutor({ supabaseClient });
 *
 * Options:
 *   supabaseClient  (required) Supabase client — used to fetch the session token.
 *   getProblem      (optional) () => ({ slug, title, description }).
 *                   Defaults to reading ?slug= / the file name, the page <h1>, and
 *                   the element marked with [data-ai-statement].
 *   apiUrl          (optional) defaults to "/api/ai-tutor".
 *
 * Security notes:
 *   - The Gemini key never touches the browser; we only send the user's Supabase JWT.
 *   - User text is rendered with textContent. AI replies are Markdown → HTML via
 *     `marked`, then sanitized with DOMPurify before insertion.
 */

const MARKED_URL = 'https://cdn.jsdelivr.net/npm/marked@15.0.12/+esm';
const PURIFY_URL = 'https://cdn.jsdelivr.net/npm/dompurify@3.2.6/+esm';

const REQUEST_TIMEOUT_MS = 60_000;
const MAX_STORED_MESSAGES = 40;
const MAX_HISTORY_TURNS = 10;
const MAX_CODE_CHARS = 20_000;
const MAX_QUESTION_CHARS = 4_000;

const MODES = {
  hint: { label: '💡 Get Hint', needsCode: false, prompt: 'Give me a hint for this problem.', promptWithCode: 'Give me a hint based on my current code.' },
  explain: { label: '📖 Explain Approach', needsCode: false, prompt: 'Explain the approach to solve this problem.', promptWithCode: 'Explain my code and the approach behind it.' },
  review: { label: '🔍 Review Code', needsCode: true, prompt: 'Review my code.' },
  debug: { label: '🐞 Debug', needsCode: true, prompt: 'Help me find the bug in my code.' },
  complexity: { label: '⏱️ Complexity', needsCode: true, prompt: "What's the time and space complexity of my code?" },
  chat: { label: '💬 Ask Anything', needsCode: false, prompt: '' },
};

const LANGUAGES = [
  ['python', 'Python'], ['javascript', 'JavaScript'], ['typescript', 'TypeScript'], ['java', 'Java'],
  ['cpp', 'C++'], ['c', 'C'], ['csharp', 'C#'], ['go', 'Go'], ['rust', 'Rust'], ['kotlin', 'Kotlin'], ['swift', 'Swift'],
];

const STORAGE = {
  chat: (slug) => `algohub:ai-tutor:chat:${slug}`,
  code: (slug) => `algohub:ai-tutor:code:${slug}`,
  lang: 'algohub:ai-tutor:lang',
  mode: 'algohub:ai-tutor:mode',
  attach: 'algohub:ai-tutor:attach',
  open: 'algohub:ai-tutor:open',
};

// ---------------------------------------------------------------------------
// Markdown (lazy-loaded, sanitized)
// ---------------------------------------------------------------------------

let markdownPromise = null;
function loadMarkdown() {
  markdownPromise ??= Promise.all([import(MARKED_URL), import(PURIFY_URL)])
    .then(([markedMod, purifyMod]) => {
      const { marked } = markedMod;
      const DOMPurify = purifyMod.default;
      DOMPurify.addHook('afterSanitizeAttributes', (node) => {
        if (node.tagName === 'A') {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
      });
      return (text) =>
        DOMPurify.sanitize(marked.parse(text, { gfm: true, breaks: false }), {
          USE_PROFILES: { html: true },
          FORBID_TAGS: ['style', 'form', 'input', 'button', 'textarea', 'select', 'img', 'iframe', 'video', 'audio'],
        });
    })
    .catch((err) => {
      console.warn('[ai-tutor] Markdown renderer failed to load; falling back to plain text.', err);
      markdownPromise = null; // allow a retry next time
      return null;
    });
  return markdownPromise;
}

// ---------------------------------------------------------------------------
// Storage helpers (never throw — private mode / quota errors are non-fatal)
// ---------------------------------------------------------------------------

const store = {
  get(area, key, fallback = null) {
    try { const v = area.getItem(key); return v === null ? fallback : v; } catch { return fallback; }
  },
  set(area, key, value) {
    try { area.setItem(key, value); } catch { /* ignore */ }
  },
  remove(area, key) {
    try { area.removeItem(key); } catch { /* ignore */ }
  },
};

// ---------------------------------------------------------------------------
// Default problem context
// ---------------------------------------------------------------------------

function defaultGetProblem() {
  const params = new URLSearchParams(location.search);
  const fromPath = location.pathname.split('/').pop().replace(/\.html$/, '');
  const slug = params.get('slug') || fromPath || 'general';
  const title = (document.querySelector('#prob-title, main h1')?.textContent || '').trim();
  const statementEl = document.querySelector('[data-ai-statement]');
  const description = statementEl ? statementEl.innerText.trim().slice(0, 7_500) : '';
  return { slug, title, description };
}

// ---------------------------------------------------------------------------
// Styles (self-contained so the component works on every page style)
// ---------------------------------------------------------------------------

const CSS = `
.aht-root {
  --aht-w: min(440px, 100vw);
  --aht-bg: #ffffff; --aht-border: #e4e4e7; --aht-ink: #09090b; --aht-soft: #71717a; --aht-rail: #f4f4f5;
  --aht-accent: #09090b; --aht-accent-ink: #ffffff; --aht-accent-soft: #f4f4f5;
  --aht-bad: #ef4444; --aht-bad-soft: #fef2f2; --aht-code-bg: #fafafa;
  --aht-shadow: 0 20px 50px -12px rgba(0, 0, 0, .18);
  font-family: 'Geist', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--aht-ink);
  letter-spacing: -0.01em;
}
html.dark .aht-root {
  --aht-bg: #0a0a0a; --aht-border: #27272a; --aht-ink: #f4f4f5; --aht-soft: #a1a1aa; --aht-rail: #111111;
  --aht-accent: #ffffff; --aht-accent-ink: #09090b; --aht-accent-soft: #18181b;
  --aht-bad: #fb7185; --aht-bad-soft: rgba(251, 113, 133, 0.12); --aht-code-bg: #141414;
  --aht-shadow: 0 24px 60px -12px rgba(0, 0, 0, .85);
}
.aht-root *, .aht-root *::before, .aht-root *::after { box-sizing: border-box; }
.aht-root :focus-visible { outline: 2px solid var(--aht-accent); outline-offset: 2px; }
.aht-root button, .aht-root select { cursor: pointer; font: inherit; }

/* Launcher - Sleek Vercel Glassmorphism */
.aht-launcher {
  position: fixed; right: 24px; bottom: 24px; z-index: 90;
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 18px; border-radius: 999px;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  background: rgba(10, 10, 10, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 13.5px; font-weight: 600; letter-spacing: -0.01em;
  box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all .2s cubic-bezier(0.16, 1, 0.3, 1);
}
.aht-launcher:hover {
  transform: translateY(-2px);
  background: rgba(20, 20, 20, 0.85);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 16px 36px -6px rgba(0, 0, 0, 0.75), 0 0 16px -2px rgba(255, 255, 255, 0.15);
}
.aht-launcher svg { width: 16px; height: 16px; color: #ffffff; }
.aht-root.is-open .aht-launcher { opacity: 0; pointer-events: none; transform: translateY(8px); }

/* Backdrop (small screens only) */
.aht-backdrop {
  position: fixed; inset: 0; z-index: 94; background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  opacity: 0; pointer-events: none; transition: opacity .25s;
}
@media (max-width: 767px) {
  .aht-root.is-open .aht-backdrop { opacity: 1; pointer-events: auto; }
}

/* Panel */
.aht-panel {
  position: fixed; top: 0; right: 0; bottom: 0; z-index: 95;
  width: var(--aht-w); display: flex; flex-direction: column;
  background: var(--aht-bg); border-left: 1px solid var(--aht-border); box-shadow: var(--aht-shadow);
  transform: translateX(100%); visibility: hidden;
  transition: transform .3s cubic-bezier(.16, 1, .3, 1), visibility 0s linear .3s;
}
.aht-root.is-open .aht-panel { transform: none; visibility: visible; transition: transform .3s cubic-bezier(.16, 1, .3, 1); }
@media (prefers-reduced-motion: reduce) {
  .aht-panel, .aht-launcher, .aht-backdrop { transition: none !important; }
}
@media (min-width: 1280px) {
  body { transition: padding-right .3s cubic-bezier(.16, 1, .3, 1); }
  body.aht-push { padding-right: var(--aht-push-w, 440px); }
}

.aht-header {
  display: flex; align-items: center; gap: 10px; padding: 14px 18px;
  border-bottom: 1px solid var(--aht-border);
  background: var(--aht-bg);
}
.aht-avatar {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0; display: grid; place-items: center;
  background: #18181b; border: 1px solid var(--aht-border); color: #fff;
}
.aht-avatar svg { width: 15px; height: 15px; }
.aht-titles { min-width: 0; flex: 1; }
.aht-title { margin: 0; font-size: 14.5px; font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; }
.aht-subtitle { margin: 2px 0 0; font-size: 11.5px; color: var(--aht-soft); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.aht-icon-btn {
  width: 30px; height: 30px; display: grid; place-items: center; flex-shrink: 0;
  border: 1px solid transparent; border-radius: 50%; background: transparent; color: var(--aht-soft);
  transition: all .15s ease;
}
.aht-icon-btn:hover { background: var(--aht-rail); color: var(--aht-ink); transform: translateY(-1px); }
.aht-icon-btn svg { width: 15px; height: 15px; }

.aht-toolbar {
  display: flex; align-items: center; gap: 8px; padding: 9px 18px;
  border-bottom: 1px solid var(--aht-border); background: var(--aht-rail);
}
.aht-toolbar label { font-size: 11.5px; font-weight: 600; color: var(--aht-soft); text-transform: uppercase; letter-spacing: 0.05em; }
.aht-select {
  appearance: none; -webkit-appearance: none;
  padding: 6px 28px 6px 10px; border-radius: 7px; border: 1px solid var(--aht-border);
  background: var(--aht-bg) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20' fill='%23a1a1aa'%3E%3Cpath d='M5.3 7.3a1 1 0 0 1 1.4 0L10 10.6l3.3-3.3a1 1 0 1 1 1.4 1.4l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 0 1 0-1.4z'/%3E%3C/svg%3E") no-repeat right 8px center / 13px;
  color: var(--aht-ink); font-size: 12.5px; font-weight: 600;
  transition: border-color .15s ease;
}
.aht-select:hover { border-color: #52525b; }
.aht-select.is-grow { flex: 1; }

/* Messages */
.aht-log { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 14px; overscroll-behavior: contain; }
.aht-msg { display: flex; flex-direction: column; max-width: 100%; }
.aht-msg.is-user { align-items: flex-end; }
.aht-bubble { border-radius: 12px; padding: 10px 14px; font-size: 13.5px; line-height: 1.6; overflow-wrap: anywhere; }
.aht-msg.is-user .aht-bubble {
  background: var(--aht-accent); color: var(--aht-accent-ink);
  border-bottom-right-radius: 4px; max-width: 88%; white-space: pre-wrap;
  font-weight: 500; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
.aht-msg.is-model .aht-bubble {
  background: var(--aht-rail); border: 1px solid var(--aht-border);
  border-bottom-left-radius: 4px; color: var(--aht-ink);
}
.aht-msg.is-error .aht-bubble {
  background: var(--aht-bad-soft); color: var(--aht-bad);
  border: 1px solid color-mix(in srgb, var(--aht-bad) 35%, transparent);
}
.aht-meta { display: flex; gap: 6px; align-items: center; margin-top: 5px; font-size: 11px; color: var(--aht-soft); }
.aht-chip { display: inline-block; padding: 1px 7px; border-radius: 999px; background: var(--aht-rail); border: 1px solid var(--aht-border); font-weight: 600; }
.aht-retry { border: 0; background: none; padding: 0; color: #10b981; font-size: 11px; font-weight: 600; text-decoration: underline; }

/* Markdown inside AI bubbles */
.aht-md > :first-child { margin-top: 0; }
.aht-md > :last-child { margin-bottom: 0; }
.aht-md p, .aht-md ul, .aht-md ol, .aht-md pre, .aht-md blockquote, .aht-md table { margin: 0 0 10px; }
.aht-md ul, .aht-md ol { padding-left: 18px; }
.aht-md ul { list-style: disc; } .aht-md ol { list-style: decimal; }
.aht-md li { margin: 3px 0; }
.aht-md h1, .aht-md h2, .aht-md h3, .aht-md h4 { margin: 14px 0 6px; font-size: 14px; font-weight: 700; line-height: 1.35; color: #ffffff; }
.aht-md a { color: #10b981; text-decoration: underline; }
.aht-md strong { font-weight: 700; color: #ffffff; }
.aht-md code { font-family: 'Geist Mono', 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; padding: 1px 5px; border-radius: 5px; background: var(--aht-code-bg); border: 1px solid var(--aht-border); }
.aht-md pre { position: relative; padding: 12px; border-radius: 8px; background: var(--aht-code-bg); border: 1px solid var(--aht-border); overflow-x: auto; }
.aht-md pre code { padding: 0; border: 0; background: none; font-size: 12px; line-height: 1.6; white-space: pre; }
.aht-md blockquote { padding-left: 10px; border-left: 2px solid var(--aht-border); color: var(--aht-soft); }
.aht-md table { border-collapse: collapse; font-size: 12.5px; display: block; overflow-x: auto; }
.aht-md th, .aht-md td { border: 1px solid var(--aht-border); padding: 5px 8px; text-align: left; }
.aht-md hr { border: 0; border-top: 1px solid var(--aht-border); margin: 12px 0; }
.aht-copy {
  position: absolute; top: 6px; right: 6px; padding: 2px 9px; border-radius: 999px;
  border: 1px solid var(--aht-border); background: var(--aht-rail); color: var(--aht-soft);
  font-size: 10.5px; font-weight: 600; opacity: 0; transition: all .15s;
}
.aht-md pre:hover .aht-copy, .aht-copy:focus-visible { opacity: 1; }
.aht-copy:hover { color: #fff; border-color: #52525b; transform: translateY(-1px); }
@media (hover: none) { .aht-copy { opacity: 1; } }

/* Welcome */
.aht-welcome { text-align: center; padding: 20px 8px 4px; color: var(--aht-soft); font-size: 13px; line-height: 1.6; }
.aht-welcome strong { display: block; color: var(--aht-ink); font-size: 15px; margin-bottom: 4px; letter-spacing: -0.01em; }
.aht-suggestions { display: flex; flex-wrap: wrap; gap: 7px; justify-content: center; margin-top: 14px; }
.aht-suggestion {
  padding: 6px 14px; border-radius: 999px; border: 1px solid var(--aht-border); background: var(--aht-bg);
  color: var(--aht-ink); font-size: 12px; font-weight: 500; transition: all .15s ease;
}
.aht-suggestion:hover { border-color: #52525b; background: var(--aht-rail); transform: translateY(-1px); }

/* Typing indicator */
.aht-typing { display: inline-flex; gap: 4px; padding: 14px 16px; }
.aht-typing span { width: 6px; height: 6px; border-radius: 50%; background: var(--aht-soft); animation: aht-bounce 1.2s infinite ease-in-out; }
.aht-typing span:nth-child(2) { animation-delay: .15s; }
.aht-typing span:nth-child(3) { animation-delay: .3s; }
@keyframes aht-bounce { 0%, 80%, 100% { transform: translateY(0); opacity: .45; } 40% { transform: translateY(-4px); opacity: 1; } }

/* Code section */
.aht-code { border-top: 1px solid var(--aht-border); }
.aht-code > summary {
  list-style: none; display: flex; align-items: center; gap: 8px; padding: 10px 18px;
  font-size: 12.5px; font-weight: 600; cursor: pointer; user-select: none; color: var(--aht-soft);
  transition: color .15s ease;
}
.aht-code > summary:hover { color: var(--aht-ink); }
.aht-code > summary::-webkit-details-marker { display: none; }
.aht-code > summary .aht-caret { width: 14px; height: 14px; color: var(--aht-soft); transition: transform .2s; }
.aht-code[open] > summary .aht-caret { transform: rotate(90deg); }
.aht-code-status { margin-left: auto; font-size: 11px; font-weight: 600; color: var(--aht-soft); }
.aht-code-body { padding: 0 18px 12px; display: flex; flex-direction: column; gap: 8px; }
.aht-code-row { display: flex; align-items: center; gap: 8px; }
.aht-check { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--aht-soft); margin-left: auto; cursor: pointer; }
.aht-check input { accent-color: var(--aht-accent); }
.aht-code-input {
  width: 100%; min-height: 150px; max-height: 38vh; resize: vertical; padding: 10px 12px;
  border-radius: 8px; border: 1px solid var(--aht-border); background: var(--aht-code-bg); color: var(--aht-ink);
  font-family: 'Geist Mono', 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; line-height: 1.55;
  tab-size: 4; white-space: pre; overflow: auto;
}
.aht-code-input:focus { outline: none; border-color: #52525b; }
.aht-code.is-flash { animation: aht-flash 1s ease; }
@keyframes aht-flash { 0%, 100% { background: transparent; } 30% { background: var(--aht-accent-soft); } }

/* Composer */
.aht-composer { padding: 12px 18px 14px; border-top: 1px solid var(--aht-border); background: var(--aht-bg); }
.aht-input-wrap {
  display: flex; align-items: flex-end; gap: 8px; padding: 6px 6px 6px 12px;
  border-radius: 10px; border: 1px solid var(--aht-border); background: var(--aht-rail);
  transition: all .15s ease;
}
.aht-input-wrap:focus-within { border-color: #71717a; box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.08); }
.aht-input {
  flex: 1; width: 100%; border: 0; outline: none; resize: none; background: transparent; color: var(--aht-ink);
  font: inherit; font-size: 13.5px; line-height: 1.5; padding: 6px 0;
  field-sizing: content; height: auto; min-block-size: 1lh; max-block-size: 8lh; overflow-y: auto;
}
@supports not (field-sizing: content) { .aht-input { height: 4.5em; } }
.aht-input::placeholder { color: var(--aht-soft); }
.aht-root .aht-input:focus-visible { outline: none; }
.aht-send {
  width: 32px; height: 32px; flex-shrink: 0; display: grid; place-items: center; border: 0; border-radius: 50%;
  background: var(--aht-accent); color: var(--aht-accent-ink); transition: all .15s ease;
}
.aht-send:hover:not(:disabled) { transform: translateY(-1px); background: #e4e4e7; }
.aht-send:disabled { opacity: .35; cursor: not-allowed; }
.aht-send svg { width: 15px; height: 15px; }
.aht-hint { margin: 6px 2px 0; font-size: 11px; color: var(--aht-soft); }
.aht-sr { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
`;

// ---------------------------------------------------------------------------
// Markup
// ---------------------------------------------------------------------------

const ICONS = {
  sparkle: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l1.9 5.6L19.5 9.5l-5.6 1.9L12 17l-1.9-5.6L4.5 9.5l5.6-1.9L12 2zm7 11l.9 2.6 2.6.9-2.6.9L19 20l-.9-2.6-2.6-.9 2.6-.9L19 13zM5 15l.7 1.8 1.8.7-1.8.7L5 20l-.7-1.8-1.8-.7 1.8-.7L5 15z"/></svg>',
  close: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  trash: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M5 7l1 12a2 2 0 002 2h8a2 2 0 002-2l1-12M9 7V4h6v3"/></svg>',
  send: '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
  caret: '<svg class="aht-caret" aria-hidden="true" viewBox="0 0 20 20" fill="currentColor"><path d="M7.3 5.3a1 1 0 011.4 0l4 4a1 1 0 010 1.4l-4 4a1 1 0 01-1.4-1.4L10.6 10 7.3 6.7a1 1 0 010-1.4z"/></svg>',
};

function buildMarkup() {
  const modeOptions = Object.entries(MODES).map(([v, m]) => `<option value="${v}">${m.label}</option>`).join('');
  const langOptions = LANGUAGES.map(([v, l]) => `<option value="${v}">${l}</option>`).join('');
  return `
    <button type="button" class="aht-launcher" data-el="launcher" aria-controls="aht-panel" aria-expanded="false">
      ${ICONS.sparkle}<span>AI Tutor</span>
    </button>
    <div class="aht-backdrop" data-el="backdrop" aria-hidden="true"></div>
    <aside class="aht-panel" id="aht-panel" data-el="panel" role="complementary" aria-labelledby="aht-title" inert>
      <header class="aht-header">
        <div class="aht-avatar">${ICONS.sparkle}</div>
        <div class="aht-titles">
          <h2 class="aht-title" id="aht-title">AI Tutor</h2>
          <p class="aht-subtitle" data-el="subtitle">Powered by Gemini</p>
        </div>
        <button type="button" class="aht-icon-btn" data-el="clear" aria-label="Clear conversation" title="Clear conversation">${ICONS.trash}</button>
        <button type="button" class="aht-icon-btn" data-el="close" aria-label="Close AI Tutor" title="Close (Esc)">${ICONS.close}</button>
      </header>

      <div class="aht-toolbar">
        <label for="aht-mode">Mode</label>
        <select id="aht-mode" class="aht-select is-grow" data-el="mode">${modeOptions}</select>
      </div>

      <div class="aht-log" data-el="log" role="log" aria-live="polite" aria-relevant="additions" tabindex="0" aria-label="Conversation"></div>

      <details class="aht-code" data-el="codeSection">
        <summary>${ICONS.caret}<span>Your code</span><span class="aht-code-status" data-el="codeStatus">Empty</span></summary>
        <div class="aht-code-body">
          <div class="aht-code-row">
            <label for="aht-lang" class="aht-sr">Language</label>
            <select id="aht-lang" class="aht-select" data-el="lang">${langOptions}</select>
            <label class="aht-check"><input type="checkbox" data-el="attach" checked> Attach to messages</label>
          </div>
          <label for="aht-code-input" class="aht-sr">Your code</label>
          <textarea id="aht-code-input" class="aht-code-input" data-el="code" spellcheck="false" autocapitalize="off" autocomplete="off"
            maxlength="${MAX_CODE_CHARS}" placeholder="Paste or write your solution here…"></textarea>
        </div>
      </details>

      <form class="aht-composer" data-el="form">
        <div class="aht-input-wrap">
          <label for="aht-input" class="aht-sr">Message the AI tutor</label>
          <textarea id="aht-input" class="aht-input" data-el="input" rows="1" maxlength="${MAX_QUESTION_CHARS}" placeholder="Ask a question…"></textarea>
          <button type="submit" class="aht-send" data-el="send" aria-label="Send message">${ICONS.send}</button>
        </div>
        <p class="aht-hint">Enter to send · Shift+Enter for a new line</p>
      </form>
    </aside>
  `;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

let instance = null;

export function initAITutor({ supabaseClient = null, getProblem = defaultGetProblem, apiUrl = '/api/ai-tutor' } = {}) {
  if (instance) return instance;

  // Inject styles once.
  const style = document.createElement('style');
  style.id = 'aht-styles';
  style.textContent = CSS;
  document.head.appendChild(style);

  const root = document.createElement('div');
  root.className = 'aht-root';
  root.innerHTML = buildMarkup();
  document.body.appendChild(root);

  const el = {};
  root.querySelectorAll('[data-el]').forEach((node) => { el[node.dataset.el] = node; });

  const slug = () => getProblem().slug || 'general';
  const state = {
    messages: loadMessages(),
    pending: null, // AbortController of the in-flight request
  };

  // ---- Restore preferences ------------------------------------------------
  el.mode.value = MODES[store.get(localStorage, STORAGE.mode)] ? store.get(localStorage, STORAGE.mode) : 'hint';
  el.lang.value = store.get(localStorage, STORAGE.lang, 'python');
  if (!el.lang.value) el.lang.value = 'python';
  el.attach.checked = store.get(localStorage, STORAGE.attach, 'true') !== 'false';
  el.code.value = store.get(localStorage, STORAGE.code(slug()), '');
  updateCodeStatus();
  updatePlaceholder();
  renderAll();

  // ---- Open / close -------------------------------------------------------
  function open() {
    root.classList.add('is-open');
    el.panel.inert = false;
    el.launcher.setAttribute('aria-expanded', 'true');
    document.body.style.setProperty('--aht-push-w', `${el.panel.offsetWidth || 440}px`);
    document.body.classList.add('aht-push');
    store.set(sessionStorage, STORAGE.open, '1');
    refreshSubtitle();
    loadMarkdown(); // warm up the renderer
    scrollToBottom();
    requestAnimationFrame(() => el.input.focus({ preventScroll: true }));
  }

  function close() {
    root.classList.remove('is-open');
    el.panel.inert = true;
    el.launcher.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('aht-push');
    store.remove(sessionStorage, STORAGE.open);
    el.launcher.focus({ preventScroll: true });
  }

  const isOpen = () => root.classList.contains('is-open');

  el.launcher.addEventListener('click', open);
  el.close.addEventListener('click', close);
  el.backdrop.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen() && !e.defaultPrevented) close();
  });

  // ---- Controls -----------------------------------------------------------
  el.mode.addEventListener('change', () => {
    store.set(localStorage, STORAGE.mode, el.mode.value);
    updatePlaceholder();
    if (MODES[el.mode.value].needsCode && !el.code.value.trim()) revealCode();
  });
  el.lang.addEventListener('change', () => { store.set(localStorage, STORAGE.lang, el.lang.value); updateCodeStatus(); });
  el.attach.addEventListener('change', () => { store.set(localStorage, STORAGE.attach, String(el.attach.checked)); updateCodeStatus(); });

  let codeSaveTimer;
  el.code.addEventListener('input', () => {
    updateCodeStatus();
    clearTimeout(codeSaveTimer);
    codeSaveTimer = setTimeout(() => store.set(localStorage, STORAGE.code(slug()), el.code.value), 300);
  });

  el.clear.addEventListener('click', () => {
    if (state.messages.length && !confirm('Clear this conversation?')) return;
    state.pending?.abort();
    state.messages = [];
    saveMessages();
    renderAll();
    el.input.focus();
  });

  // IME-safe Enter-to-send (Shift+Enter inserts a newline).
  el.input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (e.isComposing || e.keyCode === 229) return;
      el.form.requestSubmit();
    }
  });

  el.form.addEventListener('submit', (e) => {
    e.preventDefault();
    send();
  });

  el.log.addEventListener('click', (e) => {
    const suggestion = e.target.closest('[data-suggest-mode]');
    if (suggestion) {
      el.mode.value = suggestion.dataset.suggestMode;
      el.mode.dispatchEvent(new Event('change'));
      if (!MODES[el.mode.value].needsCode || el.code.value.trim()) send();
      return;
    }
    const retry = e.target.closest('[data-retry]');
    if (retry) {
      const idx = Number(retry.dataset.retry);
      const failed = state.messages[idx];
      if (failed?.request) {
        state.messages.splice(idx, 1);
        saveMessages();
        renderAll();
        send(failed.request);
      }
    }
  });

  // ---- Sending ------------------------------------------------------------
  async function send(retryRequest = null) {
    if (state.pending) return;

    const request = retryRequest || buildRequest();
    if (!request) return;

    if (!retryRequest) {
      state.messages.push({ role: 'user', text: request.displayText, mode: request.mode, codeInfo: request.codeInfo });
      el.input.value = '';
    }
    saveMessages();
    renderAll();

    const typing = appendTyping();
    setPending(true);

    const controller = new AbortController();
    state.pending = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), REQUEST_TIMEOUT_MS);

    try {
      let token = null;
      try {
        if (supabaseClient && supabaseClient.auth && typeof supabaseClient.auth.getSession === 'function') {
          const { data: { session } = {} } = await supabaseClient.auth.getSession();
          token = session?.access_token || null;
        }
      } catch (authErr) {
        console.warn('[ai-tutor] Session check error (proceeding anonymously):', authErr);
      }

      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const endpoint = apiUrl || '/api/ai-tutor';
      const res = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(request.payload),
        signal: controller.signal,
      });

      let data = {};
      try { data = await res.json(); } catch { /* non-JSON error page */ }

      if (!res.ok || typeof data.reply !== 'string') {
        const errMsg = data.error || friendlyStatus(res.status);
        throw Object.assign(new Error(errMsg), { status: res.status });
      }

      state.messages.push({ role: 'model', text: data.reply });
    } catch (err) {
      if (controller.signal.aborted && controller.signal.reason !== 'timeout') {
        // Cancelled by the user (e.g. cleared chat) — stay silent.
      } else {
        const message = controller.signal.reason === 'timeout'
          ? 'The tutor took too long to respond. Please try again.'
          : (err?.message || 'Network error — check your connection and try again.');
        state.messages.push({ role: 'error', text: message, request: err?.status === 401 ? null : request });
      }
    } finally {
      clearTimeout(timeout);
      typing.remove();
      state.pending = null;
      setPending(false);
      saveMessages();
      renderAll();
    }
  }

  function buildRequest() {
    const mode = el.mode.value;
    const cfg = MODES[mode];
    const code = el.code.value.trim();
    const typed = el.input.value.trim();
    const includeCode = Boolean(code) && (cfg.needsCode || el.attach.checked);

    if (cfg.needsCode && !code) {
      revealCode();
      flashError(`"${cfg.label.replace(/^\S+\s/, '')}" needs your code — paste it in the "Your code" section.`);
      return null;
    }
    if (!typed && mode === 'chat') {
      el.input.focus();
      return null;
    }

    const question = typed || (includeCode && cfg.promptWithCode) || cfg.prompt;
    const problem = getProblem();

    const payload = {
      mode,
      question,
      history: state.messages
        .filter((m) => m.role === 'user' || m.role === 'model')
        .slice(-MAX_HISTORY_TURNS)
        .map((m) => ({ role: m.role, text: m.text })),
    };
    if (includeCode) {
      payload.code = code;
      payload.language = el.lang.value;
    }
    if (problem.title || problem.description) {
      payload.problem = {};
      if (problem.title) payload.problem.title = problem.title.slice(0, 200);
      if (problem.description) payload.problem.description = problem.description;
    }

    const codeInfo = includeCode ? `${langLabel(el.lang.value)} · ${lineCount(code)} lines` : null;
    return { mode, payload, displayText: question, codeInfo };
  }

  // ---- Rendering ----------------------------------------------------------
  function renderAll() {
    el.log.replaceChildren();
    if (!state.messages.length) {
      el.log.appendChild(renderWelcome());
      return;
    }
    state.messages.forEach((m, i) => el.log.appendChild(renderMessage(m, i)));
    scrollToBottom();
  }

  function renderWelcome() {
    const wrap = document.createElement('div');
    wrap.className = 'aht-welcome';
    const title = document.createElement('strong');
    title.textContent = 'Stuck? I can help. 👋';
    const body = document.createElement('div');
    body.textContent = 'Ask for a hint, get your code reviewed, or debug a failing solution. Paste your code below for code-aware help.';
    const chips = document.createElement('div');
    chips.className = 'aht-suggestions';
    [['hint', '💡 Give me a hint'], ['explain', '📖 Explain the approach'], ['review', '🔍 Review my code'], ['debug', '🐞 Find my bug']].forEach(([mode, label]) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'aht-suggestion';
      b.dataset.suggestMode = mode;
      b.textContent = label;
      chips.appendChild(b);
    });
    wrap.append(title, body, chips);
    return wrap;
  }

  function renderMessage(m, index) {
    const wrap = document.createElement('div');
    wrap.className = `aht-msg is-${m.role}`;
    const bubble = document.createElement('div');
    bubble.className = 'aht-bubble';
    wrap.appendChild(bubble);

    if (m.role === 'model') {
      bubble.classList.add('aht-md');
      renderMarkdownInto(bubble, m.text);
    } else {
      bubble.textContent = m.text; // never innerHTML for user/error text
    }

    if (m.role === 'user') {
      const meta = document.createElement('div');
      meta.className = 'aht-meta';
      const modeChip = document.createElement('span');
      modeChip.className = 'aht-chip';
      modeChip.textContent = MODES[m.mode]?.label || m.mode;
      meta.appendChild(modeChip);
      if (m.codeInfo) {
        const codeChip = document.createElement('span');
        codeChip.className = 'aht-chip';
        codeChip.textContent = `📎 ${m.codeInfo}`;
        meta.appendChild(codeChip);
      }
      wrap.appendChild(meta);
    }

    if (m.role === 'error' && m.request) {
      const meta = document.createElement('div');
      meta.className = 'aht-meta';
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'aht-retry';
      retry.dataset.retry = String(index);
      retry.textContent = 'Retry';
      meta.appendChild(retry);
      wrap.appendChild(meta);
    }
    return wrap;
  }

  async function renderMarkdownInto(container, text) {
    container.textContent = text; // instant, safe placeholder
    container.style.whiteSpace = 'pre-wrap';
    const render = await loadMarkdown();
    if (!render || !container.isConnected) return;
    container.style.whiteSpace = '';
    container.innerHTML = render(text); // sanitized by DOMPurify
    container.querySelectorAll('pre').forEach(addCopyButton);
    scrollToBottom();
  }

  function addCopyButton(pre) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'aht-copy';
    btn.textContent = 'Copy';
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(pre.querySelector('code')?.innerText ?? pre.innerText);
        btn.textContent = 'Copied!';
      } catch {
        btn.textContent = 'Failed';
      }
      setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
    });
    pre.appendChild(btn);
  }

  function appendTyping() {
    const wrap = document.createElement('div');
    wrap.className = 'aht-msg is-model';
    wrap.innerHTML = '<div class="aht-bubble aht-typing" role="status" aria-label="AI tutor is typing"><span></span><span></span><span></span></div>';
    el.log.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function flashError(text) {
    state.messages.push({ role: 'error', text });
    renderAll();
    // Don't persist validation errors.
    state.messages.pop();
  }

  // ---- Small helpers ------------------------------------------------------
  function setPending(isPending) {
    el.send.disabled = isPending;
    el.form.setAttribute('aria-busy', String(isPending));
  }

  function scrollToBottom() {
    requestAnimationFrame(() => { el.log.scrollTop = el.log.scrollHeight; });
  }

  function revealCode() {
    el.codeSection.open = true;
    el.codeSection.classList.remove('is-flash');
    void el.codeSection.offsetWidth; // restart animation
    el.codeSection.classList.add('is-flash');
    el.code.focus({ preventScroll: true });
  }

  function updateCodeStatus() {
    const code = el.code.value.trim();
    el.codeStatus.textContent = code
      ? `${langLabel(el.lang.value)} · ${lineCount(code)} lines${el.attach.checked ? '' : ' · not attached'}`
      : 'Empty';
  }

  function updatePlaceholder() {
    const mode = el.mode.value;
    el.input.placeholder = mode === 'chat'
      ? 'Ask a question…'
      : `Optional: add details, or just press Enter (${MODES[mode].label.replace(/^\S+\s/, '')})`;
  }

  function refreshSubtitle() {
    const { title } = getProblem();
    el.subtitle.textContent = title ? `Helping with: ${title}` : 'Powered by Gemini';
  }

  function loadMessages() {
    try {
      const parsed = JSON.parse(store.get(sessionStorage, STORAGE.chat(slug()), '[]'));
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function saveMessages() {
    const trimmed = state.messages.slice(-MAX_STORED_MESSAGES);
    state.messages = trimmed;
    store.set(sessionStorage, STORAGE.chat(slug()), JSON.stringify(trimmed));
  }

  // Re-open automatically if the panel was open before a page navigation.
  if (store.get(sessionStorage, STORAGE.open) === '1') open();

  instance = { open, close, toggle: () => (isOpen() ? close() : open()) };
  return instance;
}

function friendlyStatus(status) {
  if (status === 401) return 'Please sign in again to use the AI tutor.';
  if (status === 429) return 'Too many requests — please wait a moment and try again.';
  if (status >= 500) return 'The AI tutor is temporarily unavailable. Please try again.';
  return 'Something went wrong. Please try again.';
}

function langLabel(value) {
  return LANGUAGES.find(([v]) => v === value)?.[1] || value;
}

function lineCount(text) {
  return text ? text.split('\n').length : 0;
}
