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
        return {
            "Authorization": f"Api-Key {get_yandex_api_key_env()}",
            "Content-Type": "application/json",
        }

    def _get_folder_id(self) -> str:
        return get_yandex_cloud_folder_id_env() or ""

    async def search_image(self, query: str) -> str | None:
        """Search Yandex Images. Returns image URL or None."""
        headers = self._get_headers()
        words = query.split()

        # Up to 3 attempts, simplifying query each time
        for attempt in range(3):
            if attempt == 1 and len(words) > 1:
                query = " ".join(words[:-1])
            elif attempt == 2:
                query = " ".join(words[:2])

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
                "folderId": self._get_folder_id(),
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.SEARCH_URL,
                        headers=headers,
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status != 200:
                            error = await resp.text()
                            print(f"Yandex Image Search error ({resp.status}): {error[:200]}")
                            return None
                        xml_text = await resp.text()
            except Exception as e:
                print(f"Yandex Image Search request error: {e}")
                return None

            url = self._parse_image_url_from_xml(xml_text)
            if url:
                return url
            print(f"Yandex Image Search: 0 results for '{query}' (attempt {attempt + 1}/3)")

        return None

    def _parse_image_url_from_xml(self, xml_text: str) -> str | None:
        """Extract first image URL from Yandex Search XML response."""
        try:
            root = ET.fromstring(xml_text)
            # Search for url elements in any namespace
            for elem in root.iter():
                if elem.tag.endswith("}url") or elem.tag == "url":
                    if elem.text and elem.text.startswith("http"):
                        return elem.text
            # Fallback: try finding <doc> elements
            for doc in root.iter():
                if doc.tag.endswith("}doc") or doc.tag == "doc":
                    for child in doc:
                        if (child.tag.endswith("}url") or child.tag == "url") and child.text:
                            return child.text
        except ET.ParseError as e:
            print(f"Yandex XML parse error: {e}")
        return None

    async def generate_image(self, prompt: str, output_directory: str) -> str | None:
        """Generate image with YandexART. Returns file path or None."""
        headers = self._get_headers()
        body = {
            "modelUri": f"art://{self._get_folder_id()}/yandex-art/latest",
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
                # Submit generation request
                async with session.post(
                    self.ART_URL,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        print(f"YandexART submit error ({resp.status}): {error[:200]}")
                        return None
                    result = await resp.json()

                operation_id = result.get("id")
                if not operation_id:
                    print("YandexART: no operation_id returned")
                    return None

                # Poll for completion
                for _ in range(30):  # 30 * 2s = 60s max
                    await asyncio.sleep(2)
                    async with session.get(
                        f"{self.OPERATION_URL}/{operation_id}",
                        headers={"Authorization": headers["Authorization"]},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as poll_resp:
                        if poll_resp.status != 200:
                            continue
                        poll_data = await poll_resp.json()
                        if poll_data.get("done"):
                            image_b64 = poll_data.get("response", {}).get("image")
                            if not image_b64:
                                print("YandexART: done but no image in response")
                                return None
                            image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                            with open(image_path, "wb") as f:
                                f.write(base64.b64decode(image_b64))
                            return image_path

                print("YandexART: timeout waiting for generation")
                return None

        except Exception as e:
            print(f"YandexART error: {e}")
            return None

    async def get_image(
        self, prompt: str, output_directory: str, image_type: str = "photo"
    ) -> str | None:
        """Route by image_type: illustration → YandexART, others → search with fallback."""
        if image_type == "illustration":
            result = await self.generate_image(prompt, output_directory)
            if result:
                return result
            # Fallback to search
            return await self.search_image(prompt)

        # photo / diagram → search first
        result = await self.search_image(prompt)
        if result:
            return result

        # Fallback to YandexART generation
        print(f"Yandex: search failed, falling back to YandexART for '{prompt[:50]}'")
        return await self.generate_image(prompt, output_directory)
