from langchain.tools import tool
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from bs4 import BeautifulSoup
from tavily import TavilyClient
from rich import print
from dotenv import load_dotenv
load_dotenv()


tavily = TavilyClient(api_key = os.getenv("TAVILY_API_KEY"))


# ─── Resilient HTTP session with automatic retries ────────────────────────────
def _build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,          # waits 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session

_session = _build_session()


# Web Search Tool
@tool
def web_search(query: str) -> str:
    """ Search the web for recent and reliable information on the topic. Returns Titles, URLs, and snippets."""

    results = tavily.search(query = query, num_results = 5)
    out = []

    for res in results['results']:
        title   = res['title']
        url     = res['url']
        content = res['content']
        out.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")

    return "\n-----\n".join(out)


# Scrape URL Tool
@tool
def scrape_url(url: str) -> str:
    """Scrape the content of a URL and return it."""

    try:
        response = _session.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        return soup.get_text(separator = " ", strip = True)[:3000]
    
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


# print(web_search.invoke("Tell me the recent news about F1"))
# print(scrape_url.invoke("https://www.espn.com/f1"))