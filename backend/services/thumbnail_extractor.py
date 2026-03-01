from __future__ import annotations

import re
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

HEADERS_FBBOT = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Facebookbot/1.0; "
        "+https://developers.facebook.com/docs/sharing/webmasters/crawler)"
    )
}


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if any(d in host for d in ["youtube.com", "youtu.be"]):
        return "youtube"
    if "tiktok.com" in host:
        return "tiktok"
    if "instagram.com" in host:
        return "instagram"
    if "facebook.com" in host or "fb.com" in host or "fb.watch" in host:
        return "facebook"
    return "generic"


def scrape_og_image(url: str, headers: dict | None = None) -> str | None:
    headers = headers or HEADERS_BROWSER
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    selectors = [
        {"property": "og:image"},
        {"name": "og:image"},
        {"property": "og:image:url"},
        {"name": "twitter:image"},
        {"name": "twitter:image:src"},
        {"itemprop": "image"},
        {"name": "thumbnail"},
    ]
    for sel in selectors:
        tag = soup.find("meta", sel)
        if tag and tag.get("content"):
            return tag["content"].strip()

    img = soup.find("img")
    if img and img.get("src"):
        return urljoin(url, img["src"])
    return None


def extract_youtube_id(url: str) -> str | None:
    patterns = [
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/watch\?.*v=([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        r"youtube\.com/v/([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_thumbnail(url: str) -> str | None:
    video_id = extract_youtube_id(url)
    if not video_id:
        return None

    qualities = ["maxresdefault", "sddefault", "hqdefault", "mqdefault", "default"]
    for quality in qualities:
        thumb_url = f"https://i.ytimg.com/vi/{video_id}/{quality}.jpg"
        try:
            resp = requests.head(thumb_url, timeout=5)
            if resp.status_code == 200:
                return thumb_url
        except Exception:
            continue

    try:
        oembed = requests.get(
            f"https://www.youtube.com/oembed?url={url}&format=json",
            timeout=10,
        ).json()
        return oembed.get("thumbnail_url")
    except Exception:
        return None


def get_tiktok_thumbnail(url: str) -> str | None:
    try:
        oembed_url = f"https://www.tiktok.com/oembed?url={url}"
        data = requests.get(oembed_url, headers=HEADERS_BROWSER, timeout=10).json()
        thumb = data.get("thumbnail_url")
        if thumb:
            return thumb
    except Exception:
        pass
    return scrape_og_image(url)


def get_instagram_thumbnail(url: str) -> str | None:
    return scrape_og_image(url, headers=HEADERS_BROWSER)


def get_facebook_thumbnail(url: str) -> str | None:
    thumb = scrape_og_image(url, headers=HEADERS_FBBOT)
    if thumb:
        return thumb
    return scrape_og_image(url, headers=HEADERS_BROWSER)


def extract_thumbnail_url(url: str) -> str | None:
    platform = detect_platform(url)
    extractors = {
        "youtube": get_youtube_thumbnail,
        "tiktok": get_tiktok_thumbnail,
        "instagram": get_instagram_thumbnail,
        "facebook": get_facebook_thumbnail,
        "generic": lambda u: scrape_og_image(u),
    }
    extractor = extractors.get(platform, extractors["generic"])
    return extractor(url)


def extract_video_heading(url: str) -> str | None:
    platform = detect_platform(url)

    if platform == "youtube":
        try:
            data = requests.get(
                f"https://www.youtube.com/oembed?url={url}&format=json",
                timeout=10,
            ).json()
            title = data.get("title")
            if isinstance(title, str) and title.strip():
                return title.strip()
        except Exception:
            pass

    if platform == "tiktok":
        try:
            data = requests.get(
                f"https://www.tiktok.com/oembed?url={url}",
                headers=HEADERS_BROWSER,
                timeout=10,
            ).json()
            title = data.get("title")
            if isinstance(title, str) and title.strip():
                return title.strip()
        except Exception:
            pass

    try:
        resp = requests.get(url, headers=HEADERS_BROWSER, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for sel in [{"property": "og:title"}, {"name": "og:title"}, {"name": "twitter:title"}]:
            tag = soup.find("meta", sel)
            content = tag.get("content") if tag else None
            if isinstance(content, str) and content.strip():
                return content.strip()

        title_tag = soup.find("title")
        if title_tag and isinstance(title_tag.text, str) and title_tag.text.strip():
            return title_tag.text.strip()
    except Exception:
        return None

    return None
