# Presenton x zachet.ai Integration Report

## New Files
- **`servers/fastapi/services/wikimedia_provider.py`** - Wikimedia Commons image search provider for educational diagrams/schemas

## Modified Files (12 total)

### 1. API Endpoint: `generate-from-document`
**`servers/fastapi/api/v1/ppt/endpoints/presentation.py`** (+488 lines)
- `POST /api/v1/ppt/presentation/generate-from-document` - accepts multipart/form-data with .docx file, `callback_url`, and `metadata` JSON. Returns `{presentation_id, status: "processing"}` immediately, runs generation in background
- `GET /api/v1/ppt/presentation/{id}/status` - returns `{status, progress (0-100), message}` for polling fallback
- `GET /api/v1/ppt/presentation/{id}/export/pptx` - direct file download
- `GET /api/v1/ppt/presentation/{id}/export/pdf` - direct file download
- Background task with webhook callback on completion/failure

### 2. Tiered Image System
**`servers/fastapi/enums/image_provider.py`** - Added `TIERED = "tiered"` enum value

**`servers/fastapi/utils/image_provider.py`** - Added `is_tiered_selected()` helper

**`servers/fastapi/services/image_generation_service.py`** (+116 lines)
- `fetch_image_tiered()` - routes by `__image_type__`: photo -> Pixabay, diagram -> Wikimedia -> Pixabay fallback, illustration -> GPT Image 1.5
- `get_image_from_pixabay_enhanced()` - supports `image_type`, `category`, `orientation`, `min_width`, `order`, `safesearch` params

### 3. System Prompt Enhancement
**`servers/fastapi/utils/llm_calls/generate_slide_content.py`** - Added `__image_type__` field instructions with mapping rules (photo/diagram/illustration), presentation context parameter, hyper-specific prompt examples

### 4. Asset Pipeline
**`servers/fastapi/utils/process_slides.py`** - Passes `__image_type__` from slide content to `generate_image()`

### 5. Bearer Auth
**`servers/fastapi/api/middlewares.py`** - `BearerAuthMiddleware` validates `Authorization: Bearer {API_SECRET_KEY}` on `/api/v1/ppt/` endpoints (only active when `API_SECRET_KEY` env is set)

**`servers/fastapi/api/main.py`** - Registered the middleware

**`servers/fastapi/utils/get_env.py`** - Added `get_api_secret_key_env()` and `get_webhook_secret_env()`

### 6. Railway/Infra
**`nginx.conf`** - Uses `${NGINX_PORT}` variable instead of hardcoded `80`

**`start.js`** - `prepareNginxConfig()` replaces `${NGINX_PORT}` with `$PORT` env (defaults to 80). Added `API_SECRET_KEY` and `WEBHOOK_SECRET` to userConfig

**`Dockerfile`** - Added `ENV PORT=80` default

---

## API Usage

### Generate presentation from document

```
POST /api/v1/ppt/presentation/generate-from-document
Authorization: Bearer {API_SECRET_KEY}
Content-Type: multipart/form-data

file: <.docx binary>
callback_url: "https://zachet360.ru/api/webhooks/presenton"
metadata: {
  "work_id": "clx123abc",
  "work_type": "essay",
  "topic": "Влияние AI на образование",
  "n_slides": 10,
  "language": "Russian",
  "include_title_slide": true,
  "include_toc_slide": false,
  "tone": "educational",
  "template": "general"
}
```

Response (instant):
```json
{
  "presentation_id": "pres_abc123",
  "status": "processing"
}
```

### Poll status (fallback if webhook fails)

```
GET /api/v1/ppt/presentation/{id}/status
Authorization: Bearer {API_SECRET_KEY}
```

Response:
```json
{
  "status": "processing",
  "progress": 60,
  "message": "Generating slides"
}
```

### Webhook callback (on completion)

```
POST {callback_url}
Authorization: Bearer {WEBHOOK_SECRET}

{
  "presentation_id": "pres_abc123",
  "work_id": "clx123abc",
  "status": "completed",
  "download_url": "/api/v1/ppt/presentation/pres_abc123/export/pptx",
  "error": null
}
```

### Download result

```
GET /api/v1/ppt/presentation/{id}/export/pptx
GET /api/v1/ppt/presentation/{id}/export/pdf
Authorization: Bearer {API_SECRET_KEY}
```

---

## Environment Variables for Railway

```
LLM=anthropic
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ANTHROPIC_MODEL=claude-sonnet-4-20250514
IMAGE_PROVIDER=tiered
OPENAI_API_KEY=${OPENAI_API_KEY}         # For AI illustrations
PIXABAY_API_KEY=${PIXABAY_API_KEY}       # For photos
API_SECRET_KEY=${API_SECRET_KEY}         # Bearer auth token
WEBHOOK_SECRET=${WEBHOOK_SECRET}         # For callback verification
CAN_CHANGE_KEYS=false
DISABLE_IMAGE_GENERATION=false
WEB_GROUNDING=false
PORT=${PORT}                             # Railway sets dynamically
DATABASE_URL=${DATABASE_URL}             # Railway Postgres (optional)
```

---

## Tiered Image System

| `__image_type__` | Primary Source | Fallback | Use Case |
|---|---|---|---|
| `photo` | Pixabay (enhanced: photo, horizontal, min 1280px, popular) | Wikimedia Commons | Historical events, real places, people, nature |
| `diagram` | Wikimedia Commons | Pixabay (illustration, science category) | Diagrams, schemes, charts, infographics |
| `illustration` | OpenAI GPT Image 1.5 (~$0.034/image) | Pixabay (basic) | Abstract concepts, decorative slides, futuristic scenarios |
