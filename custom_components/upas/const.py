"""Costanti per l'integrazione Un Posto al Sole."""
from __future__ import annotations

DOMAIN = "upas"
PLATFORMS = ["sensor", "calendar", "event", "button"]

CONF_SCAN_INTERVAL = "scan_interval"
CONF_NEWS_ENABLED = "news_enabled"
CONF_MAX_NEWS = "max_news"
CONF_MASTHEAD_TITLE = "masthead_title"
CONF_AIR_TIME = "air_time"
CONF_NEWS_SOURCES = "news_sources"
CONF_NEWS_BLOCKLIST = "news_blocklist"

DEFAULT_MASTHEAD_TITLE = "Un Posto al Sole"
DEFAULT_AIR_TIME = "20:50"
EPISODE_MINUTES = 25

DEFAULT_SCAN_INTERVAL = 360  # minuti
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 1440
DEFAULT_MAX_NEWS = 10

USER_AGENT = (
    "Mozilla/5.0 (compatible; HomeAssistant-UPAS/1.0; "
    "+https://github.com/stefanodr/ha-upas)"
)
REQUEST_TIMEOUT = 20

# Fonte delle trame settimanali (pubblicate di norma il sabato per la settimana dopo).
PLOTS_BASE = "https://www.sorrisi.com"
PLOTS_TAG_URL = f"{PLOTS_BASE}/tag/un-posto-al-sole/"
PLOTS_ARTICLE_URL = (
    PLOTS_BASE + "/tv/soap/un-posto-al-sole-le-trame-dal-{span}-{year}/"
)
PLOTS_SOURCE_NAME = "TV Sorrisi e Canzoni"

# Seconda fonte (ripiego): DiLei. Gli URL contengono un id numerico non
# prevedibile e la pagina indice non e' leggibile: gli articoli si scoprono
# dal feed di Bing News (ricerca ristretta al sito).
ALT_SOURCE_NAME = "DiLei"
ALT_DISCOVERY_URL = (
    "https://www.bing.com/news/search?"
    "q=site%3Adilei.it+%22un+posto+al+sole%22+anticipazioni+settimana&format=rss&setlang=it&cc=IT"
)
ALT_ARTICLE_MARK = "un-posto-al-sole-anticipazioni-trame-settimana-"

# Notizie generali: feed RSS (solo titolo, testata e data), unite e deduplicate.
NEWS_URL = (
    "https://news.google.com/rss/search?"
    "q=%22Un+posto+al+sole%22+when:14d&hl=it&gl=IT&ceid=IT:it"
)
NEWS_URL_BING = (
    "https://www.bing.com/news/search?"
    "q=%22Un+posto+al+sole%22&format=rss&setlang=it&cc=IT"
)
NEWS_FEEDS = {"google": NEWS_URL, "bing": NEWS_URL_BING}
NEWS_URLS = tuple(NEWS_FEEDS.values())

# La soap va in onda dal lunedì al venerdì.
EPISODE_DAYS = 5

# Lunghezza massima dell'estratto mostrato per ogni giorno: il testo completo
# resta sulla fonte originale, raggiungibile dal link "Leggi tutto".
EXCERPT_CHARS = 280

FRONTEND_URL_BASE = "/upas_static"
CARD_FILENAME = "upas-card.js"

# Archivio persistente delle ultime settimane (serve per "ieri in onda",
# per il recap e come riserva quando la fonte e' irraggiungibile).
STORAGE_KEY = "upas_archive"
STORAGE_VERSION = 1
ARCHIVE_WEEKS = 12

# Eventi (bus e entita' event)
EVENT_WEEK_PUBLISHED = "week_published"
EVENT_EPISODE_STARTING = "episode_starting"
BUS_EVENT = "upas_event"

# Repairs: dopo quanti aggiornamenti falliti consecutivi segnalare il problema
ISSUE_FAILURES = 4
ISSUE_SOURCES = "sources_unreachable"
