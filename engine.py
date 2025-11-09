from auth import NETLIFY_SITE_ID, NETLIFY_TOKEN

TRACKING_FILE = "seen_links.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1'
}

RSS_FEEDS = {
    "Jamaica Gleaner": "https://www.jamaica-gleaner.com/feed/news.xml",
    "Jamaica Observer": "https://www.jamaicaobserver.com/app-feed-category/?category=news",
    "Radio Jamaica Online": "https://radiojamaicanewsonline.com/feed/news",
    "Jamaica Information Service": "https://jis.gov.jm/feed/"
}

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/120.0.0.0 Safari/537.36')

BAR_CHAR = "▊"  # The (U+258A) character
MAX_BAR_WIDTH = 45  # Max width in characters for the longest bar

NETLIFY_SITE_ID = NETLIFY_SITE_ID
NETLIFY_TOKEN = NETLIFY_TOKEN
