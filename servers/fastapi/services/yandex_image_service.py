import asyncio
import base64
import os
import uuid
import xml.etree.ElementTree as ET

import aiohttp

from utils.get_env import get_yandex_api_key_env, get_yandex_cloud_folder_id_env


class YandexImageService:
    SEARCH_URL = "https://searchapi.api.cloud.yandex.net/v2/image/search"
    ART_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
    OPERATION_URL = "https://operation.api.cloud.yandex.net/operations"

    def _get_headers(self) -> dict:
        api_key = get_yandex_api_key_env()
        print(f"[Yandex] Using API key: {api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else f"[Yandex] API key: {api_key}")
        return {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json",
        }

    def _get_folder_id(self) -> str:
        folder_id = get_yandex_cloud_folder_id_env() or ""
        print(f"[Yandex] Folder ID: {folder_id}")
        return folder_id

    async def search_image(self, query: str) -> str | None:
        """Search Yandex Images. Returns image URL or None."""
        print(f"[Yandex Search] Starting search for: '{query}'")
        headers = self._get_headers()
        folder_id = self._get_folder_id()
        words = query.split()

        for attempt in range(3):
            if attempt == 1 and len(words) > 1:
                query = " ".join(words[:-1])
                print(f"[Yandex Search] Simplified query (attempt 2): '{query}'")
            elif attempt == 2:
                query = " ".join(words[:2])
                print(f"[Yandex Search] Minimal query (attempt 3): '{query}'")

            body = {
                "query": {
                    "searchType": "SEARCH_TYPE_RU",
                    "queryText": query,
                    "familyMode": "FAMILY_MODE_STRICT",
                },
                "imageSpec": {
                    "format": "IMAGE_FORMAT_JPEG",
                    "size": "IMAGE_SIZE_LARGE",
                    "orientation": "IMAGE_ORIENTATION_HORIZONTAL",
                },
                "docsOnPage": "5",
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
                        xml_text = await resp.text()
                        print(f"[Yandex Search] Got XML response ({len(xml_text)} bytes)")
            except Exception as e:
                print(f"[Yandex Search] Request exception: {type(e).__name__}: {e}")
                return None

            url = self._parse_image_url_from_xml(xml_text)
            if url:
                print(f"[Yandex Search] Found image: {url[:100]}")
                return url
            print(f"[Yandex Search] 0 results for '{query}' (attempt {attempt + 1}/3)")

        print(f"[Yandex Search] All 3 attempts failed")
        return None

    def _parse_image_url_from_xml(self, xml_text: str) -> str | None:
        """Extract first image URL from Yandex Search XML response."""
        try:
            root = ET.fromstring(xml_text)
            urls_found = []
            for elem in root.iter():
                if elem.tag.endswith("}url") or elem.tag == "url":
                    if elem.text and elem.text.startswith("http"):
                        urls_found.append(elem.text)
            if urls_found:
                print(f"[Yandex Search] Parsed {len(urls_found)} URLs from XML, using first")
                return urls_found[0]
            # Fallback: try finding <doc> elements
            for doc in root.iter():
                if doc.tag.endswith("}doc") or doc.tag == "doc":
                    for child in doc:
                        if (child.tag.endswith("}url") or child.tag == "url") and child.text:
                            print(f"[Yandex Search] Found URL via <doc> fallback")
                            return child.text
            print(f"[Yandex Search] No URLs found in XML. Root tag: {root.tag}, children: {[c.tag for c in root][:10]}")
        except ET.ParseError as e:
            print(f"[Yandex Search] XML parse error: {e}")
            print(f"[Yandex Search] XML preview: {xml_text[:500]}")
        return None

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
                    print(f"[YandexART] Submit response status: {resp.status}")
                    if resp.status != 200:
                        error = await resp.text()
                        print(f"[YandexART] Submit error: {error[:500]}")
                        return None
                    result = await resp.json()
                    print(f"[YandexART] Submit response: {result}")

                operation_id = result.get("id")
                if not operation_id:
                    print("[YandexART] No operation_id in response")
                    return None
                print(f"[YandexART] Operation ID: {operation_id}")

                for poll_num in range(30):  # 30 * 2s = 60s max
                    await asyncio.sleep(2)
                    poll_url = f"{self.OPERATION_URL}/{operation_id}"
                    async with session.get(
                        poll_url,
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
                                print(f"[YandexART] Done but no image. Response keys: {list(poll_data.get('response', {}).keys())}")
                                return None
                            image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                            with open(image_path, "wb") as f:
                                f.write(base64.b64decode(image_b64))
                            print(f"[YandexART] Image saved: {image_path} ({len(image_b64)} bytes b64)")
                            return image_path

                print("[YandexART] Timeout after 60s polling")
                return None

        except Exception as e:
            print(f"[YandexART] Exception: {type(e).__name__}: {e}")
            return None

    async def get_image(
        self, prompt: str, output_directory: str, image_type: str = "photo"
    ) -> str | None:
        """Route by image_type: illustration → YandexART, others → search with fallback."""
        print(f"[Yandex] get_image: type={image_type}, prompt='{prompt[:60]}'")

        if image_type == "illustration":
            print(f"[Yandex] Routing to YandexART (illustration)")
            result = await self.generate_image(prompt, output_directory)
            if result:
                print(f"[Yandex] YandexART success")
                return result
            print(f"[Yandex] YandexART failed, falling back to search")
            return await self.search_image(prompt)

        print(f"[Yandex] Routing to Yandex Image Search ({image_type})")
        result = await self.search_image(prompt)
        if result:
            print(f"[Yandex] Search success")
            return result

        print(f"[Yandex] Search failed, falling back to YandexART")
        return await self.generate_image(prompt, output_directory)
