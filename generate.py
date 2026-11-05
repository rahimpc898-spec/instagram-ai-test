import os, json, random, re, html
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT = Path("site")
OUT.mkdir(exist_ok=True)

POST_W, POST_H = 1080, 1350
FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

# Optional envs
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip()
META_HANDLE = os.getenv("META_HANDLE", "@wistfulforever").strip() or "@wistfulforever"
PEXELS_QUERIES = [
    q.strip() for q in os.getenv(
        "PEXELS_QUERIES",
        "candid girl portrait aesthetic|mirror selfie aesthetic|cozy bedroom aesthetic|couple candid aesthetic|soft lifestyle portrait|moody portrait indoors|warm aesthetic selfie|dreamy candid portrait|night city portrait aesthetic|romantic candid photo|soft girl aesthetic room|vintage style candid portrait"
    ).split("|") if q.strip()
]

USER_AGENT = "rahim-instagram-ai/1.0"


def clean_json_text(raw: str) -> str:
    raw = raw.strip()
    # remove ```json ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def call_gemini_json(prompt: str) -> dict:
    models = []
    if GEMINI_MODEL:
        models.append(GEMINI_MODEL)
    models += ["gemini-2.5-flash", "gemini-2.0-flash"]

    last_error = None
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.95
            }
        }
        try:
            r = requests.post(
                url,
                headers={
                    "x-goog-api-key": GEMINI_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            if not r.ok:
                last_error = f"{model}: {r.status_code} {r.text[:300]}"
                continue

            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = clean_json_text(text)
            return json.loads(text)
        except Exception as e:
            last_error = f"{model}: {e}"
            continue

    raise RuntimeError(f"Gemini failed on all models. Last error: {last_error}")


def fallback_copy(query: str) -> dict:
    fallback_quotes = [
        "i wish i was cuddling you rn",
        "you look like my comfort place",
        "come here and ruin my sleep",
        "you feel like a safe dream",
        "i miss you in soft ways",
        "you make my mind go quiet",
        "i want your arms tonight",
        "you’re my favorite little ache",
        "i’d choose your face again",
        "stay close in my thoughts",
    ]
    fallback_captions = [
        "lowkey thinking about you again 🤍 #aestheticquotes",
        "soft hours only #mood",
        "this one felt a little too real",
        "for the ones who miss someone quietly",
        "cute, chaotic, and slightly obsessed",
    ]
    return {
        "quote": random.choice(fallback_quotes),
        "caption": random.choice(fallback_captions),
    }


def generate_copy(query: str) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    seed = random.randint(1000, 999999)

    prompt = f"""
You write original Instagram quote-post copy for an aesthetic quotes page called {META_HANDLE}.

Return ONLY valid JSON with exactly these keys:
- quote
- caption

Rules:
- quote: 4 to 10 words
- quote must be lowercase
- quote must feel flirty / cute / emotional / romantic / soft
- no quotation marks around the quote
- no emojis in the quote
- caption: max 120 characters
- caption can contain 0 to 2 short hashtags
- caption must be original and not copy any creator
- style inspiration theme: {query}
- tone: candid, relatable, slightly chaotic internet tone
- avoid cringe, avoid being too long, avoid clichés

Current slot: {now}
Variation seed: {seed}
""".strip()

    try:
        data = call_gemini_json(prompt)
        quote = str(data.get("quote", "")).strip().strip('"')
        caption = str(data.get("caption", "")).strip()
        if not quote or not caption:
            raise ValueError("Missing quote or caption")
        if not (4 <= len(quote.split()) <= 10):
            raise ValueError("Quote length invalid")
        return {"quote": quote.lower(), "caption": caption}
    except Exception:
        return fallback_copy(query)


def pexels_search(query: str) -> list:
    url = "https://api.pexels.com/v1/search"
    params = {
        "query": query,
        "orientation": "portrait",
        "size": "large",
        "per_page": 40,
        "page": random.randint(1, 3),
    }
    r = requests.get(
        url,
        headers={"Authorization": PEXELS_API_KEY, "User-Agent": USER_AGENT},
        params=params,
        timeout=40,
    )
    r.raise_for_status()
    photos = r.json().get("photos", [])
    random.shuffle(photos)
    return photos


def choose_photo() -> dict:
    shuffled_queries = PEXELS_QUERIES[:]
    random.shuffle(shuffled_queries)

    for query in shuffled_queries:
        photos = pexels_search(query)
        good = []
        for p in photos:
            w = p.get("width", 0)
            h = p.get("height", 0)
            src = p.get("src", {})
            if w >= 700 and h >= 900 and src:
                good.append((query, p))
        if good:
            return random.choice(good)

    raise RuntimeError("No suitable Pexels photo found")


def download_image(url: str) -> Image.Image:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


def add_dark_overlay(im: Image.Image) -> Image.Image:
    base = im.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # gentle full-image darkening
    draw.rectangle((0, 0, base.width, base.height), fill=(0, 0, 0, 65))

    # stronger top-to-bottom gradient for readable text
    for y in range(base.height):
        alpha = int(40 + (y / base.height) * 25)
        draw.line((0, y, base.width, y), fill=(0, 0, 0, alpha))

    return Image.alpha_composite(base, overlay).convert("RGB")


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, stroke_width: int):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines


def draw_quote(im: Image.Image, quote: str) -> Image.Image:
    if not Path(FONT_BOLD_ITALIC).exists():
        raise FileNotFoundError(f"Missing font: {FONT_BOLD_ITALIC}")

    draw = ImageDraw.Draw(im)
    max_text_width = int(im.width * 0.84)
    stroke_width = 5

    chosen_font = None
    chosen_lines = None

    for size in range(140, 64, -4):
        font = ImageFont.truetype(FONT_BOLD_ITALIC, size)
        lines = wrap_lines(draw, quote, font, max_text_width, stroke_width)
        if len(lines) > 5:
            continue

        line_heights = []
        line_widths = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])

        total_h = sum(line_heights) + int(size * 0.16) * (len(lines) - 1)
        widest = max(line_widths) if line_widths else 0

        if widest <= max_text_width and total_h <= int(im.height * 0.58):
            chosen_font = font
            chosen_lines = lines
            break

    if chosen_font is None:
        chosen_font = ImageFont.truetype(FONT_BOLD_ITALIC, 72)
        chosen_lines = wrap_lines(draw, quote, chosen_font, max_text_width, stroke_width)

    line_gap = int(chosen_font.size * 0.16)
    dims = []
    for line in chosen_lines:
        bbox = draw.textbbox((0, 0), line, font=chosen_font, stroke_width=stroke_width)
        dims.append((bbox[2] - bbox[0], bbox[3] - bbox[1]))

    total_height = sum(h for _, h in dims) + line_gap * (len(dims) - 1)
    y = (im.height - total_height) // 2

    for i, line in enumerate(chosen_lines):
        line_w, line_h = dims[i]
        x = (im.width - line_w) // 2

        # soft shadow
        draw.text(
            (x + 3, y + 3),
            line,
            font=chosen_font,
            fill=(0, 0, 0),
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0),
        )

        # main white italic text
        draw.text(
            (x, y),
            line,
            font=chosen_font,
            fill=(255, 255, 255),
            stroke_width=stroke_width,
            stroke_fill=(35, 35, 35),
        )

        y += line_h + line_gap

    return im


def build_html(photo: dict, quote: str, caption: str, filename: str):
    photographer = photo.get("photographer", "Unknown")
    photographer_url = photo.get("photographer_url", "https://www.pexels.com")
    photo_url = photo.get("url", "https://www.pexels.com")
    query = photo.get("_query", "")

    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(quote)}</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: #111;
      color: #fff;
      display: grid;
      place-items: center;
      min-height: 100vh;
      padding: 24px;
    }}
    .wrap {{ max-width: 420px; text-align: center; }}
    img {{ width: 100%; height: auto; border-radius: 18px; box-shadow: 0 20px 60px rgba(0,0,0,.35); }}
    .meta {{ margin-top: 14px; color: #d6d6d6; font-size: 14px; line-height: 1.5; }}
    a {{ color: #fff; }}
  </style>
</head>
<body>
  <div class="wrap">
    <img src="./{html.escape(filename)}" alt="{html.escape(quote)}">
    <div class="meta">
      <div><strong>Quote:</strong> {html.escape(quote)}</div>
      <div><strong>Caption:</strong> {html.escape(caption)}</div>
      <div><strong>Theme:</strong> {html.escape(query)}</div>
      <div>Photo via <a href="https://www.pexels.com" target="_blank" rel="noopener">Pexels</a></div>
      <div>Photo by <a href="{html.escape(photographer_url)}" target="_blank" rel="noopener">{html.escape(photographer)}</a></div>
      <div><a href="{html.escape(photo_url)}" target="_blank" rel="noopener">Original photo link</a></div>
    </div>
  </div>
</body>
</html>
"""
    (OUT / "index.html").write_text(html_content, encoding="utf-8")


def main():
    query, photo = choose_photo()
    photo["_query"] = query

    src = photo.get("src", {})
    image_url = (
        src.get("large2x")
        or src.get("large")
        or src.get("original")
        or src.get("medium")
    )
    if not image_url:
        raise RuntimeError("No image URL available from Pexels")

    copy_data = generate_copy(query)
    quote = copy_data["quote"].strip().lower()
    caption = copy_data["caption"].strip()

    raw_img = download_image(image_url)
    fitted = ImageOps.fit(raw_img, (POST_W, POST_H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    styled = add_dark_overlay(fitted)
    final_img = draw_quote(styled, quote)

    filename = "post.jpg"
    final_img.save(OUT / filename, quality=95, optimize=True)

    post_data = {
        "filename": filename,
        "caption": caption,
        "quote": quote,
        "photo_source": "Pexels",
        "photo_query": query,
        "photographer": photo.get("photographer"),
        "photographer_url": photo.get("photographer_url"),
        "photo_url": photo.get("url"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    Path("post.json").write_text(json.dumps(post_data, ensure_ascii=False, indent=2), encoding="utf-8")

    build_html(photo, quote, caption, filename)

    print("Generated:", filename)
    print("Quote:", quote)
    print("Caption:", caption)
    print("Pexels query:", query)
    print("Photographer:", photo.get("photographer"))


if __name__ == "__main__":
    main()
