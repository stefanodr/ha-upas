/* Un Posto al Sole \u2013 card Lovelace in stile quotidiano.
 * Servita automaticamente dall'integrazione `upas` (nessuna risorsa da aggiungere a mano).
 *
 * Uso:
 *   type: custom:upas-card
 *   title: La Gazzetta di Posillipo   # facoltativo
 *   max_news: 6                       # facoltativo
 *   show_news: true                   # facoltativo
 *   show_highlights: true             # facoltativo: sezione "In primo piano" quando la settimana prossima non e' ancora pubblicata
 *   show_trivia: true                 # facoltativo: "Lo sapevi che?" e "Personaggio del giorno"
 *   photos_path: /local/upas          # facoltativo: cartella locale con le tue foto <id>.jpg (vedi README)
 *   theme: light                      # facoltativo: light (default), dark, auto (segue Home Assistant)
 *   layout: full                      # facoltativo: full (default) o compact (titolo, puntata e poche notizie)
 *   spoiler_free: false               # facoltativo: sfoca le trame da oggi in poi finche' non le tocchi
 *   show_yesterday: true              # facoltativo: "Ieri in onda"
 *   show_recap: true                  # facoltativo: riepilogo della settimana scorsa (a scomparsa)
 *   language: auto                    # facoltativo: auto (lingua di Home Assistant), it, en
 *   entity: sensor.xxx                # facoltativo: trovato da solo
 */
const UPAS_VERSION = "1.1.0";

// Cerca una scheda personaggio per nome (o alias) citato nelle trame.
function findChar(list, name) {
  const n = String(name || "").toLowerCase();
  if (!n || !Array.isArray(list)) return null;
  return list.find((c) => (c.aliases || []).some((a) => String(a).toLowerCase() === n)) ||
    list.find((c) => String(c.name || "").toLowerCase().split(" ").includes(n)) || null;
}

const I18N = {
  it: {
    today_on: "oggi in onda", tonight: "Stasera in onda", next_ep: "Prossima puntata", this_week: "Questa settimana", next_week: "Settimana prossima",
    prev_week: "Settimana scorsa", yesterday: "Ieri in onda", recap: "Il riepilogo della settimana scorsa", highlights: "In primo piano",
    waiting: "in attesa delle nuove trame", not_yet: "La redazione \u00e8 al lavoro: queste trame vengono pubblicate di norma il sabato precedente.",
    full_text: "Testo integrale su", go_on: "Continua su", the_source: "la fonte", paused: "Non in onda", reveal: "Tocca per leggere (spoiler)",
    web: "Dal web", latest: "ultime notizie", no_news: "Nessuna notizia disponibile al momento.", edition: "Edizione online", updated: "Aggiornata alle",
    trivia: "Lo sapevi che?", source: "Fonte", another_pill: "un'altra pillola \u2192", another_char: "un altro personaggio \u2192", in_plot: "Nella puntata di oggi",
    char_day: "Personaggio del giorno", char_card: "Scheda personaggio", played_by: "interpretato da", weekly_chars: "Personaggi della settimana", day: "giorno", days: "giorni",
    next_air: "Prossima puntata", where: "Dove guardarla", tomorrow: "Domani", tonight2: "Stasera",
    air_txt: "Rai 3, in prima serata (circa {t}), salvo variazioni di palinsesto.",
    where_txt: "In diretta su Rai 3 dal luned\u00ec al venerd\u00ec; puntate e repliche su", pub_note: "Le nuove trame vengono pubblicate di norma il sabato.",
    no_entity: "Entit\u00e0 dell'integrazione <b>Un Posto al Sole</b> non trovata. Verifica che l'integrazione sia configurata.",
    foot: "Trame: TV Sorrisi e Canzoni \u00b7 Notizie: Google News e Bing News. Estratti a scopo informativo: il testo integrale \u00e8 sulle fonti originali. Progetto indipendente, non affiliato a Rai n\u00e9 ai produttori di \u00abUn posto al sole\u00bb.",
    ago_min: "min fa", ago_h1: "ora", ago_h: "ore", ago_d1: "ieri", ago_d: "giorni fa", locale: "it-IT",
    wd: ["domenica", "luned\u00ec", "marted\u00ec", "mercoled\u00ec", "gioved\u00ec", "venerd\u00ec", "sabato"],
    mo: ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
  },
  en: {
    today_on: "on air today", tonight: "Tonight on air", next_ep: "Next episode", this_week: "This week", next_week: "Next week",
    prev_week: "Last week", yesterday: "Yesterday on air", recap: "Last week's recap", highlights: "In the spotlight",
    waiting: "waiting for the new plots", not_yet: "The newsroom is at work: these plots are usually published the Saturday before.",
    full_text: "Full text on", go_on: "Continue on", the_source: "the source", paused: "Not on air", reveal: "Tap to read (spoiler)",
    web: "From the web", latest: "latest news", no_news: "No news available right now.", edition: "Online edition", updated: "Updated at",
    trivia: "Did you know?", source: "Source", another_pill: "another one \u2192", another_char: "another character \u2192", in_plot: "In today's episode",
    char_day: "Character of the day", char_card: "Character profile", played_by: "played by", weekly_chars: "Characters of the week", day: "day", days: "days",
    next_air: "Next episode", where: "Where to watch", tomorrow: "Tomorrow", tonight2: "Tonight",
    air_txt: "Rai 3, prime time (about {t}), subject to schedule changes.",
    where_txt: "Live on Rai 3 Monday to Friday; episodes and replays on", pub_note: "New plots are usually published on Saturdays.",
    no_entity: "The <b>Un Posto al Sole</b> integration entity was not found. Check that the integration is set up.",
    foot: "Plots: TV Sorrisi e Canzoni \u00b7 News: Google News and Bing News. Excerpts for information only: the full text is on the original sources. Independent project, not affiliated with Rai or the producers of \u00abUn posto al sole\u00bb.",
    ago_min: "min ago", ago_h1: "hour", ago_h: "hours", ago_d1: "yesterday", ago_d: "days ago", locale: "en-GB",
    wd: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    mo: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  },
};
let L = I18N.it; // lingua corrente (impostata da setConfig/hass)

const MONTHS_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];
// Etichette di settimana dal backend ("19-23 ottobre"): con la UI in inglese traduce il mese.
const trLabel = (t) => (L.locale === "en-GB" ? String(t || "").replace(/[a-z\u00e0-\u00f9]+/gi, (w) => { const i = MONTHS_IT.indexOf(w.toLowerCase()); return i < 0 ? w : L.mo[i]; }) : t);

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? esc(u) : "#");

const isoLocal = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;


const parseIso = (iso) => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};
const dayLabel = (iso) => {
  const d = parseIso(iso);
  return { wd: L.wd[d.getDay()], num: d.getDate(), mon: L.mo[d.getMonth()].slice(0, 3) };
};

const relTime = (iso) => {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const mins = Math.round((Date.now() - t) / 60000);
  if (mins < 60) return `${Math.max(mins, 1)} ${L.ago_min}`;
  const h = Math.round(mins / 60);
  if (h < 24) return L.locale === "en-GB" ? `${h} ${h === 1 ? L.ago_h1 : L.ago_h} ago` : `${h} ${h === 1 ? L.ago_h1 : L.ago_h} fa`;
  const d = Math.round(h / 24);
  return d === 1 ? L.ago_d1 : `${d} ${L.ago_d}`;
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
  const label = diff === 0 ? L.tonight2 : diff === 1 ? L.tomorrow : L.wd[t.getDay()].replace(/^./, (c) => c.toUpperCase());
  return { label, wd: L.wd[t.getDay()], num: t.getDate(), mon: L.mo[t.getMonth()] };
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

// ---- "Lo sapevi che?" e "Personaggio del giorno"
const dayNumber = (now) => Math.floor(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) / 86400000);

// Personaggio del giorno: preferisce chi e' citato nella trama di oggi, altrimenti rotazione.
const pickCharacter = (chars, todayText, now, skip) => {
  if (!chars || !chars.length) return null;
  const hit = (c) => (c.aliases || [c.name.split(" ")[0]]).some((a) => new RegExp(`(^|[^A-Za-z\u00e0-\u00ff])${a}([^A-Za-z\u00e0-\u00ff]|$)`).test(todayText || ""));
  const inPlot = chars.map((c, i) => (hit(c) ? i : -1)).filter((i) => i >= 0);
  const pool = inPlot.length ? inPlot : chars.map((_, i) => i);
  const idx = pool[(dayNumber(now) + skip) % pool.length];
  return { item: chars[idx], inPlot: inPlot.length > 0 && inPlot.includes(idx) };
};

const initials = (name) => name.split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
const safePhotoDir = (p) => (typeof p === "string" && /^\/(?!\/)[\w\-./]*$/.test(p) ? p.replace(/\/+$/, "") : "");

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
.chips span.go { cursor: pointer; border-color: var(--ink); }
.chips span.go:hover { background: var(--rule); }
.chips i { color: var(--muted); font-style: normal; font-size: 11px; margin-left: 4px; }
.trivia { border: 1px solid var(--rule); border-top: 3px double var(--rule); background: var(--soft); padding: 10px 14px 8px; margin-bottom: 14px; display: flex; gap: 14px; align-items: flex-start; }
.trivia .yr { font-size: 30px; font-weight: 700; color: var(--accent); line-height: 1; min-width: 64px; text-align: center; padding-top: 4px; }
.trivia .yr.q { font-size: 38px; }
.trivia .tb { min-width: 0; flex: 1; }
.trivia .tt { font-weight: 700; font-size: 15px; margin: 2px 0 3px; }
.trivia p { margin: 0; font-size: 14px; line-height: 1.5; }
.trivia .tf { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-size: 11.5px; color: var(--muted); margin-top: 6px; font-style: italic; }
.trivia button { font: inherit; font-style: italic; background: none; border: 0; color: var(--accent); cursor: pointer; padding: 0; text-decoration: underline; }
.tbox { border: 1px solid var(--rule); outline: 3px double var(--rule); outline-offset: 2px; padding: 12px 14px; margin: 0 0 18px 0; background: var(--soft); }
.tbox .tx { margin: 6px 0 0; font-size: 14.5px; line-height: 1.5; }
.tbox .yr { float: left; font-size: 2.1em; font-weight: 700; color: var(--accent); line-height: 1; padding: 2px 10px 0 0; }
.tbox .src { font-size: 11.5px; color: var(--muted); margin-top: 8px; font-style: italic; }
.btn { font: inherit; font-size: 12px; font-style: italic; color: var(--accent); background: none; border: 0; padding: 0; cursor: pointer; text-decoration: underline; }
.row2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0 22px; margin-bottom: 4px; }
.char { display: flex; gap: 12px; align-items: flex-start; }
.av { position: relative; flex: 0 0 64px; height: 76px; border: 1px solid var(--rule); background: var(--paper); display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 700; color: var(--accent); letter-spacing: .04em; overflow: hidden; }
.av img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.char .nm { font-size: 17px; font-weight: 700; line-height: 1.2; }
.char .by { font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-top: 2px; }
.char .an { font-style: italic; font-size: 13.5px; line-height: 1.45; margin: 6px 0 0; }
.more { font-size: 12px; font-style: italic; margin-top: 6px; }
.spoil { filter: blur(6px); cursor: pointer; user-select: none; transition: filter .2s; }
.spoil.on { filter: none; cursor: auto; user-select: text; }
.hint { font-size: 10.5px; color: var(--muted); font-style: italic; letter-spacing: .04em; }
.item.pause .d b { color: var(--muted); text-decoration: line-through; }
.item.pause p { font-style: italic; color: var(--muted); }
details.recap { border-top: 1px solid var(--rule); padding: 8px 0; margin-bottom: 12px; }
details.recap summary { cursor: pointer; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; }
.yday { border-left: 3px solid var(--muted); padding: 4px 0 4px 10px; margin: 0 0 14px; }
.yday p { margin: 2px 0 0; font-size: 13.5px; line-height: 1.45; }
.paper.compact .mast .title { font-size: clamp(18px, 4.5vw, 24px); }
.paper.compact .bar { margin-bottom: 10px; }
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
    this._config = {
      show_news: true, max_news: 6, theme: "light", show_highlights: true, show_trivia: true,
      show_yesterday: true, show_recap: true, layout: "full", spoiler_free: false, language: "auto", ...config,
    };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._revealed = this._revealed || new Set();
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const ent = this._findEntity();
    const sig = ent ? `${ent.state}|${ent.last_updated}|${isoLocal(new Date())}|${this._isDark()}|${this._lang()}` : "none";
    if (sig !== this._sig) {
      this._sig = sig;
      this._render();
    }
  }

  _lang() {
    const c = String(this._config?.language || "auto").toLowerCase();
    if (c === "it" || c === "en") return c;
    return String(this._hass?.locale?.language || this._hass?.language || "it").toLowerCase().startsWith("en") ? "en" : "it";
  }

  _isDark() {
    const t = String(this._config?.theme || "light").toLowerCase();
    if (t === "dark") return true;
    if (t === "auto") return !!this._hass?.themes?.darkMode;
    return false;
  }

  getCardSize() {
    return this._config?.layout === "compact" ? 6 : 12;
  }

  static getStubConfig() {
    return { max_news: 6, theme: "light" };
  }

  static getConfigElement() {
    return document.createElement("upas-card-editor");
  }

  _findEntity() {
    if (!this._hass) return null;
    if (this._config?.entity) return this._hass.states[this._config.entity] || null;
    const id = Object.keys(this._hass.states).find((k) => this._hass.states[k].attributes?.upas_role === "edition");
    return id ? this._hass.states[id] : null;
  }

  // Testo di una puntata; con spoiler_free le puntate da oggi in poi sono sfocate finche' non le tocchi.
  _plot(day, todayIso, cls = "") {
    const spoil = this._config.spoiler_free && day.date >= todayIso && !this._revealed.has(day.date);
    const key = esc(day.date);
    return spoil
      ? `<p class="spoil ${cls}" data-spoil="${key}" title="${esc(L.reveal)}">${esc(day.excerpt)}</p>`
      : `<p class="${cls}">${esc(day.excerpt)}</p>`;
  }

  _dayItem(day, todayIso) {
    const l = dayLabel(day.date);
    const cls = day.date === todayIso ? "today" : day.date < todayIso ? "past" : "";
    const paused = day.no_episode;
    const tag = day.date === todayIso ? ` \u00b7 ${esc(L.today_on)}` : "";
    const body = paused
      ? `<p>${esc(L.paused)}: ${esc(day.pause_note || day.excerpt)}</p>`
      : this._plot(day, todayIso);
    return `<div class="item ${cls} ${paused ? "pause" : ""}"><div class="d"><b>${esc(l.wd)}</b> ${l.num} ${esc(l.mon)}${paused ? "" : tag}</div>${body}</div>`;
  }

  _weekColumn(title, week, todayIso) {
    if (!week) return "";
    let body;
    if (!week.available) {
      body = `<div class="empty">${esc(L.not_yet)}</div>`;
    } else {
      body = week.days.map((d) => this._dayItem(d, todayIso)).join("") +
        `<div class="more">${esc(L.full_text)} <a href="${safeUrl(week.url)}" target="_blank" rel="noopener noreferrer">${esc(week.source)}</a> \u2192</div>`;
    }
    return `<section class="col"><h3 class="sect">${esc(title)}<small>${esc(trLabel(week.label))}</small></h3>${body}</section>`;
  }

  _highlights(attrs) {
    const days = [...(attrs.this_week?.days || []), ...(attrs.next_week?.days || [])];
    const nx = nextAir(new Date());
    const names = this._config.spoiler_free ? [] : featuredNames(days);
    const t = String(attrs.air_time || "20:50").slice(0, 5);
    const chips = names.length
      ? `<div class="item"><div class="d"><b>${esc(L.weekly_chars)}</b></div><p class="chips">${names.map(([n, c]) => `<span${findChar(attrs.characters, n) && this._config.show_trivia !== false ? ` class="go" data-char="${esc(n)}" role="button" tabindex="0"` : ""}>${esc(n)}<i>${c} ${c === 1 ? L.day : L.days}</i></span>`).join("")}</p></div>`
      : "";
    return `<section class="col"><h3 class="sect">${esc(L.highlights)}<small>${esc(L.waiting)}</small></h3>
      <div class="item"><div class="d"><b>${esc(L.next_air)}</b></div><p>${esc(nx.label.toLowerCase() === nx.wd ? "" : nx.label + ", ")}${esc(nx.wd)} ${nx.num} ${esc(nx.mon)} \u00b7 ${esc(L.air_txt.replace("{t}", t))}</p></div>
      ${chips}
      <div class="item"><div class="d"><b>${esc(L.where)}</b></div><p>${esc(L.where_txt)} <a href="https://www.raiplay.it/programmi/unpostoalsole" target="_blank" rel="noopener noreferrer">RaiPlay</a>.</p></div>
      <div class="more">${esc(L.pub_note)}</div></section>`;
  }

  _lead(attrs, todayIso) {
    const all = [...(attrs.this_week?.days || []), ...(attrs.next_week?.days || [])].filter((d) => !d.no_episode);
    const src = (d) => (attrs.this_week?.days || []).includes(d) ? attrs.this_week : attrs.next_week;
    const today = all.find((d) => d.date === todayIso);
    const next = all.find((d) => d.date > todayIso);
    const pick = today || next;
    if (!pick) return "";
    const { head, body } = splitHeadline(pick.excerpt);
    const l = dayLabel(pick.date);
    const kicker = today ? L.tonight : `${L.next_ep} \u00b7 ${l.wd} ${l.num} ${l.mon}`;
    const week = src(pick);
    const spoil = this._config.spoiler_free && !this._revealed.has(pick.date);
    const attr = spoil ? ` class="spoil" data-spoil="${esc(pick.date)}" title="${esc(L.reveal)}"` : "";
    const compact = this._config.layout === "compact";
    return `<section class="lead"><div class="kicker">${esc(kicker)}</div><h2${attr}>${esc(head)}</h2>${body && !compact ? `<p${attr}>${esc(body)}</p>` : ""}
      <div class="more"><a href="${safeUrl(week?.url)}" target="_blank" rel="noopener noreferrer">${esc(L.go_on)} ${esc(week?.source || L.the_source)}</a> \u2192</div></section>`;
  }

  _yesterday(attrs) {
    if (this._config.show_yesterday === false || !attrs.yesterday) return "";
    const y = attrs.yesterday;
    const l = dayLabel(y.date);
    const txt = y.no_episode ? `${L.paused}: ${y.pause_note || y.excerpt}` : y.excerpt;
    return `<section class="yday"><div class="kicker">${esc(L.yesterday)} \u00b7 ${esc(l.wd)} ${l.num} ${esc(l.mon)}</div><p>${esc(txt)}</p></section>`;
  }

  _recap(attrs) {
    const w = attrs.previous_week;
    if (this._config.show_recap === false || !w?.available) return "";
    const rows = w.days.map((d) => {
      const l = dayLabel(d.date);
      return `<div class="item"><div class="d"><b>${esc(l.wd)}</b> ${l.num} ${esc(l.mon)}</div><p>${esc(d.no_episode ? `${L.paused}: ${d.pause_note || ""}` : d.excerpt)}</p></div>`;
    }).join("");
    return `<details class="recap"><summary>${esc(L.recap)} \u00b7 ${esc(trLabel(w.label))}</summary>${rows}</details>`;
  }

  _trivia(attrs) {
    if (this._config.show_trivia === false) return "";
    const pick = pickTrivia(attrs.trivia, new Date(), this._skip || 0);
    if (!pick) return "";
    const t = pick.item;
    const year = t.year ? `<div class="yr">${esc(t.year)}</div>` : `<div class="yr q">?</div>`;
    return `<section class="trivia">${year}<div class="tb"><div class="kicker">${esc(L.trivia)}</div><div class="tt">${esc(t.title)}</div><p>${esc(t.text)}</p>
      <div class="tf"><span>${esc(L.source)}: <a href="${safeUrl(t.url)}" target="_blank" rel="noopener noreferrer">${esc(t.source)}</a></span><span>${pick.pos}/${pick.total} \u00b7 <button type="button" class="tbtn">${esc(L.another_pill)}</button></span></div></div></section>`;
  }

  _characterBox(attrs, todayIso) {
    const todayText = [...(attrs.this_week?.days || []), ...(attrs.next_week?.days || [])].filter((d) => d.date === todayIso).map((d) => d.excerpt).join(" ");
    let p = pickCharacter(attrs.characters, todayText, new Date(), this._cskip || 0);
    const chosen = this._cname ? findChar(attrs.characters, this._cname) : null;
    if (chosen) p = { item: chosen, inPlot: false, picked: true };
    if (!p) return "";
    const c = p.item;
    const dir = safePhotoDir(this._config.photos_path);
    const img = dir ? `<img src="${esc(dir)}/${esc(c.photo || c.id)}.jpg" alt="" loading="lazy">` : "";
    const inPlot = p.inPlot && !this._config.spoiler_free;
    return `<section class="tbox"><div class="kicker">${p.picked ? esc(L.char_card) : inPlot ? esc(L.in_plot) : esc(L.char_day)}</div>
      <div class="char"><div class="av">${esc(initials(c.name))}${img}</div><div>
      <div class="nm">${esc(c.name)}</div><div class="by">${esc(L.played_by)} ${esc(c.actor)}</div>
      <p class="tx">${esc(c.caption)}</p>${c.anecdote ? `<p class="an">\u00ab${esc(c.anecdote)}\u00bb</p>` : ""}</div></div>
      <div class="src">${esc(L.source)}: <a href="${safeUrl(c.url)}" target="_blank" rel="noopener noreferrer">${esc(c.source)}</a> \u00b7 <button class="btn" data-act="char">${esc(L.another_char)}</button></div></section>`;
  }

  _news(attrs) {
    if (!this._config.show_news) return "";
    const cap = this._config.layout === "compact" ? Math.min(3, Number(this._config.max_news) || 3) : Number(this._config.max_news) || 6;
    const items = (attrs.news || []).slice(0, cap);
    const body = items.length
      ? items.map((n) => `<div class="item"><a class="h" href="${safeUrl(n.url)}" target="_blank" rel="noopener noreferrer">${esc(n.title)}</a>
          <div class="m">${esc(n.source)}${n.source && n.published ? " \u00b7 " : ""}${esc(relTime(n.published))}</div></div>`).join("")
      : `<div class="empty">${esc(L.no_news)}</div>`;
    return `<section class="news"><h3 class="sect">${esc(L.web)}<small>${esc(L.latest)}</small></h3><div class="nl">${body}</div></section>`;
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    L = I18N[this._lang()];
    const ent = this._findEntity();
    const compact = this._config.layout === "compact";
    let inner;
    if (!this._hass) {
      inner = "";
    } else if (!ent) {
      inner = `<div class="err">${L.no_entity}</div>`;
    } else {
      const a = ent.attributes || {};
      const now = new Date();
      const todayIso = isoLocal(now);
      const upd = ent.state && ent.state !== "unknown" && ent.state !== "unavailable" ? new Date(ent.state) : null;
      const updTxt = upd && !Number.isNaN(upd.getTime()) ? upd.toLocaleTimeString(L.locale, { hour: "2-digit", minute: "2-digit" }) : "\u2014";
      const title = this._config.title || a.masthead_title || "Un Posto al Sole";
      const nextCol = a.next_week?.available || this._config.show_highlights === false
        ? this._weekColumn(L.next_week, a.next_week, todayIso) : this._highlights(a);
      inner = `
        <header class="mast"><div class="title"><span class="sun">\u2600</span> ${esc(title)}</div></header>
        <div class="bar"><span>${esc(L.wd[now.getDay()])} ${now.getDate()} ${esc(L.mo[now.getMonth()])} ${now.getFullYear()}</span>${compact ? "" : `<span>${esc(L.edition)}</span>`}<span>${esc(L.updated)} ${esc(updTxt)}</span></div>
        ${this._lead(a, todayIso)}
        ${compact ? "" : this._yesterday(a)}
        ${compact ? "" : `<div class="cols">${this._weekColumn(L.this_week, a.this_week, todayIso)}${nextCol}</div>`}
        ${compact ? "" : this._recap(a)}
        ${compact ? "" : this._trivia(a)}
        ${compact || this._config.show_trivia === false ? "" : this._characterBox(a, todayIso)}
        ${this._news(a)}
        <div class="foot">${esc(L.foot)}</div>`;
    }
    const dark = this._isDark();
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="paper ${dark ? "dark" : ""} ${compact ? "compact" : ""}">${inner}</div></ha-card>`;
    this.shadowRoot.querySelectorAll(".btn").forEach((b) =>
      b.addEventListener("click", () => {
        this._cskip = (this._cskip || 0) + 1;
        this._cname = null;
        this._render();
      })
    );
    this.shadowRoot.querySelectorAll("[data-char]").forEach((el) => {
      const open = () => {
        this._cname = el.dataset.char;
        this._render();
        this.shadowRoot.querySelector(".tbox")?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      };
      el.addEventListener("click", open);
      el.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    });
    this.shadowRoot.querySelectorAll("[data-spoil]").forEach((el) =>
      el.addEventListener("click", () => {
        this._revealed.add(el.dataset.spoil);
        this._render();
      })
    );
    // foto locale opzionale: se non esiste resta il monogramma
    this.shadowRoot.querySelectorAll(".av img").forEach((im) => im.addEventListener("error", () => im.remove()));
    const btn = this.shadowRoot.querySelector(".tbtn");
    if (btn) btn.addEventListener("click", () => { this._skip = (this._skip || 0) + 1; this._render(); });
  }
}

// ---- Editor visivo (Impostazioni della card)
const EDITOR_LABELS = {
  it: { title: "Titolo della testata (vuoto = dalle opzioni)", theme: "Tema", layout: "Aspetto", language: "Lingua", max_news: "Numero di notizie",
    show_news: "Mostra le notizie", show_trivia: "Mostra \u00abLo sapevi che?\u00bb e personaggio", show_highlights: "Mostra \u00abIn primo piano\u00bb",
    show_yesterday: "Mostra \u00abIeri in onda\u00bb", show_recap: "Mostra il riepilogo della settimana scorsa", spoiler_free: "Modalit\u00e0 senza spoiler",
    photos_path: "Cartella foto locali (facoltativa, es. /local/upas)", entity: "Entit\u00e0 (facoltativa)" },
  en: { title: "Masthead title (empty = from options)", theme: "Theme", layout: "Layout", language: "Language", max_news: "Number of news items",
    show_news: "Show news", show_trivia: "Show \u201cDid you know?\u201d and character", show_highlights: "Show \u201cIn the spotlight\u201d",
    show_yesterday: "Show \u201cYesterday on air\u201d", show_recap: "Show last week's recap", spoiler_free: "Spoiler-free mode",
    photos_path: "Local photos folder (optional, e.g. /local/upas)", entity: "Entity (optional)" },
};

class UpasCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._build();
  }

  _build() {
    if (!this._config) return;
    const lang = String(this._hass?.locale?.language || "it").startsWith("en") ? "en" : "it";
    const T = EDITOR_LABELS[lang];
    const opt = (v, l) => ({ value: v, label: l });
    const schema = [
      { name: "title", selector: { text: {} } },
      { name: "layout", selector: { select: { mode: "dropdown", options: [opt("full", lang === "en" ? "Full" : "Completa"), opt("compact", lang === "en" ? "Compact" : "Compatta")] } } },
      { name: "theme", selector: { select: { mode: "dropdown", options: [opt("light", lang === "en" ? "Light" : "Chiaro"), opt("dark", lang === "en" ? "Dark" : "Scuro"), opt("auto", "Auto")] } } },
      { name: "language", selector: { select: { mode: "dropdown", options: [opt("auto", "Auto"), opt("it", "Italiano"), opt("en", "English")] } } },
      { name: "max_news", selector: { number: { min: 1, max: 30, mode: "box" } } },
      { name: "show_news", selector: { boolean: {} } },
      { name: "show_trivia", selector: { boolean: {} } },
      { name: "show_highlights", selector: { boolean: {} } },
      { name: "show_yesterday", selector: { boolean: {} } },
      { name: "show_recap", selector: { boolean: {} } },
      { name: "spoiler_free", selector: { boolean: {} } },
      { name: "photos_path", selector: { text: {} } },
      { name: "entity", selector: { entity: { domain: "sensor" } } },
    ];
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        const cfg = { ...ev.detail.value };
        for (const k of Object.keys(cfg)) if (cfg[k] === "" || cfg[k] === undefined) delete cfg[k];
        this._config = { type: "custom:upas-card", ...cfg };
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = schema;
    this._form.computeLabel = (s) => T[s.name] || s.name;
    this._form.data = {
      layout: "full", theme: "light", language: "auto", max_news: 6, show_news: true, show_trivia: true,
      show_highlights: true, show_yesterday: true, show_recap: true, spoiler_free: false, ...this._config,
    };
  }
}

if (!customElements.get("upas-card")) customElements.define("upas-card", UpasCard);
if (!customElements.get("upas-card-editor")) customElements.define("upas-card-editor", UpasCardEditor);
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
