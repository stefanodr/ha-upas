# Changelog

## 1.1.0
### English
- **Second plot source (fallback):** DiLei weekly articles are used when TV Sorrisi e Canzoni has no article for a week (articles discovered via Bing News; recent weeks only). The week reports its real source. This path is fail-soft and untested against the live site, enable debug logging for `custom_components.upas` to see it at work.
- On first install the **previous week is fetched once**, so the recap is not empty until the archive fills up.
- New sensors **Next break** and **Episodes in a row**, new **Refresh now** button; the Repairs notice now has a **Retry now** action.
- **Card**: characters of the week are clickable (opens the profile); week labels are translated when the UI is in English.
- **Blueprint** `notify_tonight` (reminder before the episode, spoiler-free option).
- Weekly **source check** workflow and `scripts/check_sources.py`; 7 new trivia pills; more tests.
- No entity is renamed.

### Italiano
- **Seconda fonte per le trame (ripiego):** gli articoli settimanali di DiLei sono usati quando TV Sorrisi e Canzoni non ha l'articolo di una settimana (articoli scoperti tramite Bing News; solo settimane recenti). La settimana indica la fonte reale. Il percorso fallisce senza errori ed è stato testato solo con fixture, non sul sito reale: attiva il log di debug di `custom_components.upas` per vederlo in azione.
- Alla prima installazione la **settimana scorsa viene recuperata una volta**, così il riepilogo non resta vuoto finché l'archivio non si riempie.
- Nuovi sensori **Prossima pausa** e **Puntate di fila**, nuovo pulsante **Aggiorna ora**; l'avviso in Riparazioni ha ora l'azione **Riprova ora**.
- **Card**: personaggi della settimana cliccabili (apre la scheda); etichette delle settimane tradotte con l'interfaccia in inglese.
- **Blueprint** `notify_tonight` (promemoria prima della puntata, opzione senza spoiler).
- Workflow di **controllo settimanale delle fonti** e `scripts/check_sources.py`; 7 nuove pillole; più test.
- Nessuna entità viene rinominata.

## 1.0.0
### English
- **Yesterday on air** and a collapsible **last-week recap**, backed by a persistent archive (survives restarts, kept for 12 weeks) that is also used as a fallback when the source is unreachable.
- **Days without an episode** (breaks, sports events) are detected: new attributes `no_episode` and `pause_note`, shown in the card and in the calendar (no event on those days).
- New entities: **calendar** (episodes), **event** (`week_published`, `episode_starting`), sensors **Yesterday's episode** and **Last week**. No existing entity is renamed.
- New service **`upas.get_summary`** (returns data; for Assist/LLM and scripts) and `upas_event` bus event.
- **Card**: visual editor, `layout: compact`, `spoiler_free`, `show_yesterday`, `show_recap`, `language` (IT/EN UI); title defaults to the one set in the integration options.
- **News**: choose the sources (Google/Bing) and exclude words (title/source).
- **Options**: masthead title and air time (calendar and event).
- **Diagnostics** download and a **Repairs** notice when the sources stay unreachable.
- README now in English (`README.md`) and Italian (`README.it.md`); CI workflow (hassfest, HACS, tests); more tests.
- Not included: a second plot source (planned for 1.1).

### Italiano
- **Ieri in onda** e **riepilogo della settimana scorsa** (a scomparsa), con un archivio persistente (resta dopo i riavvii, 12 settimane) usato anche come riserva quando la fonte non risponde.
- **Giorni senza puntata** (pause, eventi sportivi) riconosciuti: nuovi attributi `no_episode` e `pause_note`, mostrati nella card e nel calendario (nessun evento in quei giorni).
- Nuove entità: **calendario** (puntate), **evento** (`week_published`, `episode_starting`), sensori **Ieri in onda** e **Settimana scorsa**. Nessuna entità esistente viene rinominata.
- Nuovo servizio **`upas.get_summary`** (restituisce dati; per Assist/LLM e script) ed evento sul bus `upas_event`.
- **Card**: editor visivo, `layout: compact`, `spoiler_free`, `show_yesterday`, `show_recap`, `language` (interfaccia IT/EN); il titolo predefinito è quello scelto nelle opzioni dell'integrazione.
- **Notizie**: scelta delle fonti (Google/Bing) ed esclusione di parole (titolo/testata).
- **Opzioni**: titolo della testata e orario di messa in onda (calendario ed evento).
- **Diagnostica** scaricabile e avviso in **Riparazioni** se le fonti restano irraggiungibili.
- README in inglese (`README.md`) e in italiano (`README.it.md`); workflow CI (hassfest, HACS, test); più test.
- Non incluso: una seconda fonte per le trame (prevista per la 1.1).

## 0.5.0
- Nuova sezione **Personaggio del giorno**: interprete, ruolo, didascalia e fonte. Se un personaggio e' citato nella trama di oggi viene scelto lui, altrimenti rotazione giornaliera.
- Foto facoltative: l'integrazione non include foto (diritti); con `photos_path` la card usa le tue immagini in `/config/www/upas/`, altrimenti mostra un monogramma.
- Nuovo sensore **Personaggio del giorno** e nuovi attributi `characters` sul sensore Edizione.
- Due nuove pillole in "Lo sapevi che?" (la "sporca dozzina", la storia sulle donazioni di sangue).

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
