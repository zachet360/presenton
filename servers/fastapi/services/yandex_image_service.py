import asyncio
import base64
import json
import os
import re
import uuid
import xml.etree.ElementTree as ET

import aiohttp

from utils.get_env import get_yandex_api_key_env, get_yandex_cloud_folder_id_env


def _normalize(text: str) -> set[str]:
    """Lowercase and split into word set for matching."""
    return set(re.sub(r"[^\w\s]", "", text.lower()).split())


def _relevance_score(result: dict, query_words: set[str]) -> float:
    """Score a search result by how many query words appear in its title/passage."""
    title_words = _normalize(result.get("title", ""))
    passage_words = _normalize(result.get("passage", ""))
    all_words = title_words | passage_words
    if not query_words:
        return 0
    return len(query_words & all_words) / len(query_words)


class YandexImageService:
    SEARCH_URL = "https://searchapi.api.cloud.yandex.net/v2/image/search"
    ART_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
    OPERATION_URL = "https://operation.api.cloud.yandex.net/operations"

    MIN_IMAGE_BYTES = 5_000  # skip tiny images / broken downloads
    MIN_IMAGE_WIDTH = 400    # skip thumbnails

    def _get_headers(self) -> dict:
        api_key = get_yandex_api_key_env()
        print(f"[Yandex] API key: {api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else f"[Yandex] API key: {api_key}")
        return {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        }

    def _get_folder_id(self) -> str:
        folder_id = get_yandex_cloud_folder_id_env() or ""
        print(f"[Yandex] Folder ID: {folder_id}")
        return folder_id

    async def _download_image(self, url: str, output_directory: str) -> str | None:
        """Download image from URL to local file. Returns local path or None."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        print(f"[Yandex Search] Download failed ({resp.status}): {url[:80]}")
                        return None
                    data = await resp.read()
                    if len(data) < self.MIN_IMAGE_BYTES:
                        print(f"[Yandex Search] Image too small ({len(data)} bytes), skipping: {url[:80]}")
                        return None
                    ext = "jpg"
                    ct = resp.headers.get("Content-Type", "")
                    if "png" in ct:
                        ext = "png"
                    elif "webp" in ct:
                        ext = "webp"
                    path = os.path.join(output_directory, f"{uuid.uuid4()}.{ext}")
                    with open(path, "wb") as f:
                        f.write(data)
                    print(f"[Yandex Search] Downloaded {len(data)} bytes → {path}")
                    return path
        except Exception as e:
            print(f"[Yandex Search] Download error for {url[:80]}: {type(e).__name__}: {e}")
            return None

    async def search_image(
        self, query: str, output_directory: str, orientation: str = "IMAGE_ORIENTATION_HORIZONTAL",
    ) -> str | None:
        """Search Yandex Images with relevance ranking. Returns file path or None."""
        print(f"[Yandex Search] Starting search for: '{query}' (orientation={orientation})")
        headers = self._get_headers()
        folder_id = self._get_folder_id()
        words = query.split()
        query_words = _normalize(query)

        for attempt in range(3):
            if attempt == 1 and len(words) > 2:
                query = " ".join(words[:3])
                query_words = _normalize(query)
                print(f"[Yandex Search] Shortened query (attempt 2): '{query}'")
            elif attempt == 2 and len(words) > 1:
                query = " ".join(words[:2])
                query_words = _normalize(query)
                print(f"[Yandex Search] Minimal query (attempt 3): '{query}'")

            image_spec = {
                "format": "IMAGE_FORMAT_JPEG",
                "size": "IMAGE_SIZE_LARGE",
            }
            if orientation:
                image_spec["orientation"] = orientation

            body = {
                "query": {
                    "searchType": "SEARCH_TYPE_RU",
                    "queryText": query,
                    "familyMode": "FAMILY_MODE_STRICT",
                },
                "imageSpec": image_spec,
                "docsOnPage": "10",
                "folderId": folder_id,
            }

            try:
                print(f"[Yandex Search] POST {self.SEARCH_URL}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.SEARCH_URL,
                        headers=headers,
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        print(f"[Yandex Search] Response status: {resp.status}")
                        if resp.status != 200:
                            error = await resp.text()
                            print(f"[Yandex Search] Error response: {error[:500]}")
                            return None
                        response_text = await resp.text()
                        print(f"[Yandex Search] Got response ({len(response_text)} bytes)")
            except Exception as e:
                print(f"[Yandex Search] Request exception: {type(e).__name__}: {e}")
                return None

            xml_text = self._extract_xml_from_response(response_text)
            if not xml_text:
                print(f"[Yandex Search] Could not extract XML from response")
                return None

            results = self._parse_results_from_xml(xml_text)
            if not results:
                print(f"[Yandex Search] 0 results for '{query}' (attempt {attempt + 1}/3)")
                continue

            # Filter out too-small images by reported dimensions
            filtered = []
            for r in results:
                w = r.get("width", 0)
                if w and w < self.MIN_IMAGE_WIDTH:
                    print(f"[Yandex Search] Skipping {r['url'][:60]} — too narrow ({w}px)")
                    continue
                filtered.append(r)
            if not filtered:
                filtered = results  # fallback: don't discard everything

            # Score by relevance to query
            for r in filtered:
                r["_score"] = _relevance_score(r, query_words)
            filtered.sort(key=lambda r: r["_score"], reverse=True)

            print(f"[Yandex Search] {len(filtered)} candidates, scores: {[round(r['_score'], 2) for r in filtered[:5]]}")

            # Download in score order
            for i, r in enumerate(filtered):
                print(f"[Yandex Search] Trying #{i + 1} (score={r['_score']:.2f}): {r['url'][:80]}")
                local_path = await self._download_image(r["url"], output_directory)
                if local_path:
                    return local_path
            print(f"[Yandex Search] All {len(filtered)} URLs failed to download (attempt {attempt + 1}/3)")

        print(f"[Yandex Search] All 3 attempts failed")
        return None

    def _extract_xml_from_response(self, response_text: str) -> str | None:
        """Extract XML from Yandex API response. Response is JSON with base64-encoded XML in rawData."""
        try:
            data = json.loads(response_text)
            raw_data = data.get("rawData")
            if raw_data:
                xml_bytes = base64.b64decode(raw_data)
                xml_text = xml_bytes.decode("utf-8")
                print(f"[Yandex Search] Decoded base64 rawData → XML ({len(xml_text)} bytes)")
                return xml_text
            print(f"[Yandex Search] JSON response but no rawData. Keys: {list(data.keys())[:10]}")
            return None
        except (json.JSONDecodeError, ValueError):
            pass

        if response_text.strip().startswith("<?xml") or response_text.strip().startswith("<"):
            print(f"[Yandex Search] Response is raw XML")
            return response_text

        print(f"[Yandex Search] Unknown response format. Preview: {response_text[:200]}")
        return None

    def _parse_results_from_xml(self, xml_text: str) -> list[dict]:
        """Parse image search results with metadata from Yandex XML response."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"[Yandex Search] XML parse error: {e}")
            return []

        ns = ""
        # Detect namespace
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        results = []

        # Find all doc/group elements that contain image results
        for doc in root.iter(f"{ns}doc"):
            url_el = doc.find(f"{ns}url")
            if url_el is None or not url_el.text or not url_el.text.startswith("http"):
                continue

            title = ""
            title_el = doc.find(f"{ns}title")
            if title_el is not None:
                title = "".join(title_el.itertext()).strip()

            passage = ""
            passage_el = doc.find(f".//{ns}passage")
            if passage_el is not None:
                passage = "".join(passage_el.itertext()).strip()

            # Try to get image dimensions from image-properties or similar
            width = 0
            height = 0
            for prop in doc.iter():
                tag = prop.tag.replace(ns, "")
                if tag == "image-properties":
                    w_attr = prop.get("width") or prop.findtext(f"{ns}width") or ""
                    h_attr = prop.get("height") or prop.findtext(f"{ns}height") or ""
                    try:
                        width = int(w_attr) if w_attr else 0
                        height = int(h_attr) if h_attr else 0
                    except ValueError:
                        pass

            results.append({
                "url": url_el.text,
                "title": title,
                "passage": passage,
                "width": width,
                "height": height,
            })

        if results:
            print(f"[Yandex Search] Parsed {len(results)} results with metadata")
        else:
            # Fallback: just grab URLs like before
            urls = []
            for elem in root.iter():
                if elem.tag.endswith("}url") or elem.tag == "url":
                    if elem.text and elem.text.startswith("http"):
                        urls.append(elem.text)
            if urls:
                print(f"[Yandex Search] Fallback: parsed {len(urls)} URLs without metadata")
                results = [{"url": u, "title": "", "passage": "", "width": 0, "height": 0} for u in urls]
            else:
                print(f"[Yandex Search] No URLs in XML. Root: {root.tag}")

        return results

    async def generate_image(self, prompt: str, output_directory: str) -> str | None:
        """Generate image with YandexART. Returns file path or None."""
        print(f"[YandexART] Starting generation for: '{prompt[:80]}'")
        headers = self._get_headers()
        folder_id = self._get_folder_id()
        body = {
            "modelUri": f"art://{folder_id}/yandex-art/latest",
            "generationOptions": {
                "seed": 1863,
                "aspectRatio": {"widthRatio": 16, "heightRatio": 9},
            },
            "messages": [
                {"weight": 1, "text": prompt}
            ],
        }

        try:
            async with aiohttp.ClientSession() as session:
                print(f"[YandexART] POST {self.ART_URL}")
                async with session.post(
                    self.ART_URL,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    print(f"[YandexART] Submit status: {resp.status}")
                    if resp.status != 200:
                        error = await resp.text()
                        print(f"[YandexART] Submit error: {error[:500]}")
                        return None
                    result = await resp.json()

                operation_id = result.get("id")
                if not operation_id:
                    print(f"[YandexART] No operation_id. Response: {result}")
                    return None
                print(f"[YandexART] Operation ID: {operation_id}")

                for poll_num in range(30):  # 30 * 2s = 60s max
                    await asyncio.sleep(2)
                    async with session.get(
                        f"{self.OPERATION_URL}/{operation_id}",
                        headers={"Authorization": headers["Authorization"]},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as poll_resp:
                        if poll_resp.status != 200:
                            print(f"[YandexART] Poll #{poll_num + 1} status: {poll_resp.status}")
                            continue
                        poll_data = await poll_resp.json()
                        done = poll_data.get("done", False)
                        if poll_num % 5 == 0 or done:
                            print(f"[YandexART] Poll #{poll_num + 1}: done={done}")
                        if done:
                            image_b64 = poll_data.get("response", {}).get("image")
                            if not image_b64:
                                print(f"[YandexART] Done but no image. Keys: {list(poll_data.get('response', {}).keys())}")
                                return None
                            image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                            with open(image_path, "wb") as f:
                                f.write(base64.b64decode(image_b64))
                            print(f"[YandexART] Saved: {image_path} ({len(image_b64)} b64 bytes)")
                            return image_path

                print("[YandexART] Timeout after 60s")
                return None

        except Exception as e:
            print(f"[YandexART] Exception: {type(e).__name__}: {e}")
            return None

    async def get_image(
        self, prompt: str, output_directory: str, image_type: str = "photo",
        orientation: str = "IMAGE_ORIENTATION_HORIZONTAL",
    ) -> str | None:
        """Route by image_type: illustration → YandexART, others → search with fallback."""
        print(f"[Yandex] get_image: type={image_type}, orientation={orientation}, prompt='{prompt[:60]}'")

        if image_type == "illustration":
            print(f"[Yandex] Routing to YandexART (illustration)")
            result = await self.generate_image(prompt, output_directory)
            if result:
                return result
            print(f"[Yandex] YandexART failed, falling back to search")
            return await self.search_image(prompt, output_directory, orientation)

        print(f"[Yandex] Routing to Yandex Image Search ({image_type})")
        result = await self.search_image(prompt, output_directory, orientation)
        if result:
            return result

        print(f"[Yandex] Search failed, falling back to YandexART")
        return await self.generate_image(prompt, output_directory)
