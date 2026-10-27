# Changelog

## 0.4.0
- Nuova sezione **Lo sapevi che?**: pillole con aneddoti e curiosità sulla storia della serie, una al giorno (con ricorrenze, ad esempio il 21 ottobre per l'anniversario della prima puntata) e il pulsante "un'altra pillola". Ogni pillola riporta la fonte.
- Nuovo sensore **Lo sapevi che** con la pillola del giorno e la sua fonte.
- Nuova opzione `show_trivia` della card (default `true`).

## 0.3.0
- Nuova sezione **In primo piano** al posto della colonna "Settimana prossima" quando le trame non sono ancora state pubblicate (di norma fino al sabato): prossima puntata (data e orario), personaggi della settimana, dove guardarla (Rai 3 e RaiPlay).
- Quando le trame della settimana successiva sono disponibili, la colonna torna a mostrarle.
- Nuova opzione `show_highlights` della card (default `true`; con `false` si vede sempre la colonna della settimana prossima).

## 0.2.1
- La risorsa della card viene aggiunta automaticamente alle risorse Lovelace (modalità storage).
- Nuova opzione `theme` della card: `light` (default), `dark`, `auto`.
- File della card scritto in ASCII (sequenze `\u`), nessun problema di codifica.

## 0.2.0
- Trame giorno per giorno della settimana corrente e della successiva (fonte: TV Sorrisi e Canzoni).
- Notizie generali dal web da due feed RSS (Google News e Bing News: titolo, testata, data), unite e deduplicate.
- Card Lovelace `custom:upas-card` in stile quotidiano, registrata automaticamente.
- Icona e logo (cartella `brand/`), traduzioni IT/EN.
- Config flow moderno con ricarica automatica alle modifiche delle opzioni; istanza unica.
- Test automatici (parser e integrazione) e workflow CI (hassfest, HACS, pytest).

## 0.1.0
- Prima versione sperimentale (scraping di link generici).
