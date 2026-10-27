/* Un Posto al Sole \u2013 card Lovelace in stile quotidiano.
 * Servita automaticamente dall'integrazione `upas` (nessuna risorsa da aggiungere a mano).
 *
 * Uso:
 *   type: custom:upas-card
 *   title: La Gazzetta di Posillipo   # facoltativo
 *   max_news: 6                       # facoltativo
 *   show_news: true                   # facoltativo
 *   show_highlights: true             # facoltativo: sezione "In primo piano" quando la settimana prossima non e' ancora pubblicata
 *   show_trivia: true                 # facoltativo: sezione "Lo sapevi che?"
 *   theme: light                      # facoltativo: light (default), dark, auto (segue Home Assistant)
 *   entity: sensor.xxx                # facoltativo: trovato da solo
 */
const UPAS_VERSION = "0.4.0";

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? esc(u) : "#");

const isoLocal = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

const WEEKDAY = ["domenica", "luned\u00ec", "marted\u00ec", "mercoled\u00ec", "gioved\u00ec", "venerd\u00ec", "sabato"];
const MONTH = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];

const parseIso = (iso) => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};
const dayLabel = (iso) => {
  const d = parseIso(iso);
  return { wd: WEEKDAY[d.getDay()], num: d.getDate(), mon: MONTH[d.getMonth()].slice(0, 3) };
};

const relTime = (iso) => {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const mins = Math.round((Date.now() - t) / 60000);
  if (mins < 60) return `${Math.max(mins, 1)} min fa`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h} ${h === 1 ? "ora" : "ore"} fa`;
  const d = Math.round(h / 24);
  return d === 1 ? "ieri" : `${d} giorni fa`;
};

// Il titolo "di giornale" \u00e8 la prima frase dell'estratto, il resto \u00e8 il sommario.
const splitHeadline = (text) => {
  const m = /^(.{25,170}?[.!?])\s+(.*)$/.exec(text || "");
  return m ? { head: m[1], body: m[2] } : { head: text || "", body: "" };
};

// ---- "In primo piano": contenuti sempre disponibili, anche senza le trame della settimana dopo.
const STOP_NAMES = new Set(["Caff\u00e8", "Vulcano", "Palazzo", "Palladini", "Napoli", "Posillipo", "Rai", "Italia", "Vesuvio", "Roma", "Milano", "Sorrisi"]);

// Personaggi citati nelle trame: nomi propri trovati a met\u00e0 frase, poi contati su quanti giorni compaiono.
const featuredNames = (days) => {
  const mid = /(?<=[a-z\u00e0-\u00f9,;:] )([A-Z\u00c0-\u00dd][a-z\u00e0-\u00ff']{2,})/g;
  const names = new Set();
  for (const d of days) {
    for (const m of (d.excerpt || "").matchAll(mid)) if (!STOP_NAMES.has(m[1])) names.add(m[1]);
  }
  const rows = [];
  for (const n of names) {
    const re = new RegExp(`(^|[^A-Za-z\u00e0-\u00ff])${n}([^A-Za-z\u00e0-\u00ff]|$)`);
    rows.push([n, days.filter((d) => re.test(d.excerpt || "")).length]);
  }
  return rows.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "it")).slice(0, 6);
};

// Prossima puntata: dal luned\u00ec al venerd\u00ec in prima serata; dopo le 21:30 si guarda al giorno dopo.
const nextAir = (now) => {
  const day0 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const late = now.getHours() > 21 || (now.getHours() === 21 && now.getMinutes() >= 30);
  const t = new Date(day0);
  const weekend = (x) => x.getDay() === 0 || x.getDay() === 6;
  if (weekend(t) || late) {
    do { t.setDate(t.getDate() + 1); } while (weekend(t));
  }
  const diff = Math.round((t - day0) / 86400000);
  const label = diff === 0 ? "Stasera" : diff === 1 ? "Domani" : WEEKDAY[t.getDay()].replace(/^./, (c) => c.toUpperCase());
  return { label, wd: WEEKDAY[t.getDay()], num: t.getDate(), mon: MONTH[t.getMonth()] };
};

// Pillola "Lo sapevi che?": ricorrenza (campo "on" = MM-DD) oppure rotazione giornaliera. Stessa formula del sensore.
const pickTrivia = (items, now, skip) => {
  if (!items || !items.length) return null;
  const mmdd = `${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const ann = items.findIndex((t) => t.on === mmdd);
  const dayNum = Math.floor(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) / 86400000);
  const idx = ((ann >= 0 ? ann : dayNum % items.length) + skip) % items.length;
  return { item: items[idx], pos: idx + 1, total: items.length };
};

const STYLE = `
:host { display: block; }
ha-card { overflow: hidden; }
.paper {
  --paper: #f5f0e4; --ink: #1d1b18; --muted: #6b6558; --rule: #1d1b18; --accent: #8a1c1c; --soft: #ebe4d3;
  background: var(--paper); color: var(--ink);
  font-family: Georgia, "Times New Roman", "Noto Serif", serif;
  padding: 16px 18px 12px;
}
.paper.dark {
  --paper: #1f1d1a; --ink: #ece6d8; --muted: #a39b8a; --rule: #ece6d8; --accent: #e07a5f; --soft: #2a2723;
}
.mast { text-align: center; }
.mast .title { font-size: clamp(22px, 5.5vw, 34px); font-weight: 700; letter-spacing: .04em; font-variant: small-caps; line-height: 1.1; }
.mast .sun { color: var(--accent); }
.bar { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
  color: var(--muted); border-top: 3px double var(--rule); border-bottom: 1px solid var(--rule); padding: 4px 0; margin: 8px 0 14px; }
.kicker { font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); font-weight: 700; margin-bottom: 4px; }
.lead { border-bottom: 1px solid var(--rule); padding-bottom: 14px; margin-bottom: 14px; }
.lead h2 { font-size: clamp(20px, 4.6vw, 28px); line-height: 1.15; margin: 0 0 8px; font-weight: 700; }
.lead p { margin: 0; font-size: 15px; line-height: 1.5; text-align: justify; hyphens: auto; }
.lead p:first-of-type::first-letter { font-size: 2.6em; float: left; line-height: .85; padding: 4px 6px 0 0; font-weight: 700; color: var(--accent); }
.cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0 22px; }
.col { padding-bottom: 12px; margin-bottom: 4px; min-width: 0; }
.cols { border-bottom: 1px solid var(--rule); margin-bottom: 14px; }
@media (min-width: 620px) { .col + .col { border-left: 1px solid var(--rule); padding-left: 22px; } }
.sect { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; border-bottom: 2px solid var(--rule); padding-bottom: 3px; margin: 0 0 8px;
  display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.sect small { font-weight: 400; letter-spacing: .04em; color: var(--muted); text-transform: none; font-style: italic; }
.item { padding: 7px 0; border-bottom: 1px dotted var(--muted); }
.item:last-of-type { border-bottom: 0; }
.item .d { font-size: 11px; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; color: var(--muted); }
.item .d b { color: var(--ink); }
.item.today { background: var(--soft); margin: 0 -8px; padding: 7px 8px; border-left: 3px solid var(--accent); }
.item.today .d b { color: var(--accent); }
.item.past { opacity: .55; }
.item p { margin: 2px 0 0; font-size: 13.5px; line-height: 1.45; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 0 !important; }
.chips span { border: 1px solid var(--rule); padding: 1px 8px; font-size: 12.5px; border-radius: 2px; }
.chips i { color: var(--muted); font-style: normal; font-size: 11px; margin-left: 4px; }
.trivia { border: 1px solid var(--rule); border-top: 3px double var(--rule); background: var(--soft); padding: 10px 14px 8px; margin-bottom: 14px; display: flex; gap: 14px; align-items: flex-start; }
.trivia .yr { font-size: 30px; font-weight: 700; color: var(--accent); line-height: 1; min-width: 64px; text-align: center; padding-top: 4px; }
.trivia .yr.q { font-size: 38px; }
.trivia .tb { min-width: 0; flex: 1; }
.trivia .tt { font-weight: 700; font-size: 15px; margin: 2px 0 3px; }
.trivia p { margin: 0; font-size: 14px; line-height: 1.5; }
.trivia .tf { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-size: 11.5px; color: var(--muted); margin-top: 6px; font-style: italic; }
.trivia button { font: inherit; font-style: italic; background: none; border: 0; color: var(--accent); cursor: pointer; padding: 0; text-decoration: underline; }
.more { font-size: 12px; font-style: italic; margin-top: 6px; }
.empty { font-style: italic; color: var(--muted); font-size: 13.5px; line-height: 1.45; padding: 6px 0; }
.news { margin-bottom: 12px; }
.nl { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0 22px; }
.nl .item { border-bottom: 1px dotted var(--muted); }
.news a.h { color: var(--ink); text-decoration: none; font-weight: 700; font-size: 14.5px; line-height: 1.3; display: block; }
.news a.h:hover { text-decoration: underline; color: var(--accent); }
.news .m { font-size: 11px; color: var(--muted); letter-spacing: .04em; margin-top: 2px; }
a { color: var(--accent); }
.foot { font-size: 10.5px; color: var(--muted); text-align: center; border-top: 1px solid var(--rule); padding-top: 6px; line-height: 1.4; }
.err { padding: 16px; font-family: sans-serif; }
`;

class UpasCard extends HTMLElement {
  setConfig(config) {
    this._config = { show_news: true, max_news: 6, theme: "light", show_highlights: true, show_trivia: true, title: "La Gazzetta di Posillipo", ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const ent = this._findEntity();
    const sig = ent ? `${ent.state}|${ent.last_updated}|${isoLocal(new Date())}|${this._isDark()}` : "none";
    if (sig !== this._sig) {
      this._sig = sig;
      this._render();
    }
  }

  _isDark() {
    const t = String(this._config?.theme || "light").toLowerCase();
    if (t === "dark") return true;
    if (t === "auto") return !!this._hass?.themes?.darkMode;
    return false;
  }

  getCardSize() {
    return 12;
  }

  static getStubConfig() {
    return { title: "La Gazzetta di Posillipo", max_news: 6, theme: "light" };
  }

  _findEntity() {
    if (!this._hass) return null;
    if (this._config?.entity) return this._hass.states[this._config.entity] || null;
    const id = Object.keys(this._hass.states).find((k) => this._hass.states[k].attributes?.upas_role === "edition");
    return id ? this._hass.states[id] : null;
  }

  _dayItem(day, todayIso) {
    const l = dayLabel(day.date);
    const cls = day.date === todayIso ? "today" : day.date < todayIso ? "past" : "";
    return `<div class="item ${cls}"><div class="d"><b>${esc(l.wd)}</b> ${l.num} ${esc(l.mon)}${day.date === todayIso ? " \u00b7 oggi in onda" : ""}</div><p>${esc(day.excerpt)}</p></div>`;
  }

  _weekColumn(title, week, todayIso) {
    if (!week) return "";
    let body;
    if (!week.available) {
      body = `<div class="empty">La redazione \u00e8 al lavoro: queste trame vengono pubblicate di norma il sabato precedente.</div>`;
    } else {
      body = week.days.map((d) => this._dayItem(d, todayIso)).join("") +
        `<div class="more">Testo integrale su <a href="${safeUrl(week.url)}" target="_blank" rel="noopener noreferrer">${esc(week.source)}</a> \u2192</div>`;
    }
    return `<section class="col"><h3 class="sect">${esc(title)}<small>${esc(week.label)}</small></h3>${body}</section>`;
  }

  _highlights(attrs) {
    const days = [...(attrs.this_week?.days || []), ...(attrs.next_week?.days || [])];
    const nx = nextAir(new Date());
    const names = featuredNames(days);
    const next = attrs.next_week;
    const range = next?.label ? `Le trame del ${esc(next.label)} saranno pubblicate di norma il sabato.` : "Le nuove trame vengono pubblicate di norma il sabato.";
    const chips = names.length
      ? `<div class="item"><div class="d"><b>Personaggi della settimana</b></div><p class="chips">${names.map(([n, c]) => `<span>${esc(n)}<i>${c} ${c === 1 ? "giorno" : "giorni"}</i></span>`).join("")}</p></div>`
      : "";
    return `<section class="col"><h3 class="sect">In primo piano<small>in attesa delle nuove trame</small></h3>
      <div class="item"><div class="d"><b>Prossima puntata</b></div><p>${esc(nx.label)}, ${esc(nx.wd)} ${nx.num} ${esc(nx.mon)} \u00b7 Rai 3, in prima serata (circa 20:50), salvo variazioni di palinsesto.</p></div>
      ${chips}
      <div class="item"><div class="d"><b>Dove guardarla</b></div><p>In diretta su Rai 3 dal luned\u00ec al venerd\u00ec; puntate e repliche su <a href="https://www.raiplay.it/programmi/unpostoalsole" target="_blank" rel="noopener noreferrer">RaiPlay</a>.</p></div>
      <div class="more">${range}</div></section>`;
  }

  _lead(attrs, todayIso) {
    const all = [...(attrs.this_week?.days || []), ...(attrs.next_week?.days || [])];
    const src = (d) => (attrs.this_week?.days || []).includes(d) ? attrs.this_week : attrs.next_week;
    const today = all.find((d) => d.date === todayIso);
    const next = all.find((d) => d.date > todayIso);
    const pick = today || next;
    if (!pick) return "";
    const { head, body } = splitHeadline(pick.excerpt);
    const l = dayLabel(pick.date);
    const kicker = today ? "Stasera in onda" : `Prossima puntata \u00b7 ${l.wd} ${l.num} ${l.mon}`;
    const week = src(pick);
    return `<section class="lead"><div class="kicker">${esc(kicker)}</div><h2>${esc(head)}</h2>${body ? `<p>${esc(body)}</p>` : ""}
      <div class="more"><a href="${safeUrl(week?.url)}" target="_blank" rel="noopener noreferrer">Continua su ${esc(week?.source || "la fonte")}</a> \u2192</div></section>`;
  }

  _trivia(attrs) {
    if (this._config.show_trivia === false) return "";
    const pick = pickTrivia(attrs.trivia, new Date(), this._skip || 0);
    if (!pick) return "";
    const t = pick.item;
    const year = t.year ? `<div class="yr">${esc(t.year)}</div>` : `<div class="yr q">?</div>`;
    return `<section class="trivia">${year}<div class="tb"><div class="kicker">Lo sapevi che?</div><div class="tt">${esc(t.title)}</div><p>${esc(t.text)}</p>
      <div class="tf"><span>Fonte: <a href="${safeUrl(t.url)}" target="_blank" rel="noopener noreferrer">${esc(t.source)}</a></span><span>${pick.pos}/${pick.total} \u00b7 <button type="button" class="tbtn">un'altra pillola \u2192</button></span></div></div></section>`;
  }

  _news(attrs) {
    if (!this._config.show_news) return "";
    const items = (attrs.news || []).slice(0, Number(this._config.max_news) || 6);
    const body = items.length
      ? items.map((n) => `<div class="item"><a class="h" href="${safeUrl(n.url)}" target="_blank" rel="noopener noreferrer">${esc(n.title)}</a>
          <div class="m">${esc(n.source)}${n.source && n.published ? " \u00b7 " : ""}${esc(relTime(n.published))}</div></div>`).join("")
      : `<div class="empty">Nessuna notizia disponibile al momento.</div>`;
    return `<section class="news"><h3 class="sect">Dal web<small>ultime notizie</small></h3><div class="nl">${body}</div></section>`;
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    const ent = this._findEntity();
    let inner;
    if (!this._hass) {
      inner = "";
    } else if (!ent) {
      inner = `<div class="err">Entit\u00e0 dell'integrazione <b>Un Posto al Sole</b> non trovata. Verifica che l'integrazione sia configurata.</div>`;
    } else {
      const a = ent.attributes || {};
      const now = new Date();
      const todayIso = isoLocal(now);
      const upd = ent.state && ent.state !== "unknown" && ent.state !== "unavailable" ? new Date(ent.state) : null;
      const updTxt = upd && !Number.isNaN(upd.getTime()) ? upd.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" }) : "\u2014";
      inner = `
        <header class="mast"><div class="title"><span class="sun">\u2600</span> ${esc(this._config.title)}</div></header>
        <div class="bar"><span>${esc(WEEKDAY[now.getDay()])} ${now.getDate()} ${esc(MONTH[now.getMonth()])} ${now.getFullYear()}</span><span>Edizione online</span><span>Aggiornata alle ${esc(updTxt)}</span></div>
        ${this._lead(a, todayIso)}
        <div class="cols">${this._weekColumn("Questa settimana", a.this_week, todayIso)}${a.next_week?.available || this._config.show_highlights === false ? this._weekColumn("Settimana prossima", a.next_week, todayIso) : this._highlights(a)}</div>
        ${this._trivia(a)}
        ${this._news(a)}
        <div class="foot">Trame: TV Sorrisi e Canzoni \u00b7 Notizie: Google News e Bing News. Estratti a scopo informativo: il testo integrale \u00e8 sulle fonti originali. Progetto indipendente, non affiliato a Rai n\u00e9 ai produttori di \u00abUn posto al sole\u00bb.</div>`;
    }
    const dark = this._isDark();
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="paper ${dark ? "dark" : ""}">${inner}</div></ha-card>`;
    const btn = this.shadowRoot.querySelector(".tbtn");
    if (btn) btn.addEventListener("click", () => { this._skip = (this._skip || 0) + 1; this._render(); });
  }
}

if (!customElements.get("upas-card")) customElements.define("upas-card", UpasCard);
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "upas-card")) {
  window.customCards.push({
    type: "upas-card",
    name: "Un Posto al Sole",
    description: "Anticipazioni della settimana e notizie in stile quotidiano.",
    preview: false,
  });
}
console.info(`%c UPAS-CARD %c ${UPAS_VERSION} `, "background:#8a1c1c;color:#fff", "background:#333;color:#fff");
