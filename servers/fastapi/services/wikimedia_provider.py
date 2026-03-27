from typing import Optional
import aiohttp


async def search_wikimedia(query: str) -> Optional[str]:
    """Search Wikimedia Commons for educational images (diagrams, schemas, etc.)"""
    url = "https://commons.wikimedia.org/w/api.php"

    # Step 1: Search for files
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",  # File namespace
        "srlimit": "5",
        "format": "json",
        "origin": "*",
    }

    try:
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

            results = data.get("query", {}).get("search", [])
            if not results:
                return None

            # Step 2: Get image URL for first result
            title = results[0]["title"]
            img_params = {
                "action": "query",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": "1280",
                "format": "json",
                "origin": "*",
            }

            async with session.get(url, params=img_params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                img_data = await resp.json()

            pages = img_data.get("query", {}).get("pages", {})
            for page in pages.values():
                imageinfo = page.get("imageinfo", [])
                if imageinfo:
                    return imageinfo[0].get("thumburl") or imageinfo[0].get("url")

    except Exception as e:
        print(f"Wikimedia search error: {e}")

    return None
