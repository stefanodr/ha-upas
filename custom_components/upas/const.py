"""Costanti per l'integrazione Un Posto al Sole."""
from __future__ import annotations

DOMAIN = "upas"
PLATFORMS = ["sensor"]

CONF_SCAN_INTERVAL = "scan_interval"
CONF_NEWS_ENABLED = "news_enabled"
CONF_MAX_NEWS = "max_news"

DEFAULT_SCAN_INTERVAL = 360  # minuti
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 1440
DEFAULT_MAX_NEWS = 10

USER_AGENT = (
    "Mozilla/5.0 (compatible; HomeAssistant-UPAS/0.2; "
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

# Notizie generali: feed RSS (solo titolo, testata e data), unite e deduplicate.
NEWS_URL = (
    "https://news.google.com/rss/search?"
    "q=%22Un+posto+al+sole%22+when:14d&hl=it&gl=IT&ceid=IT:it"
)
NEWS_URL_BING = (
    "https://www.bing.com/news/search?"
    "q=%22Un+posto+al+sole%22&format=rss&setlang=it&cc=IT"
)
NEWS_URLS = (NEWS_URL, NEWS_URL_BING)

# La soap va in onda dal lunedì al venerdì.
EPISODE_DAYS = 5

# Lunghezza massima dell'estratto mostrato per ogni giorno: il testo completo
# resta sulla fonte originale, raggiungibile dal link "Leggi tutto".
EXCERPT_CHARS = 280

FRONTEND_URL_BASE = "/upas_static"
CARD_FILENAME = "upas-card.js"
