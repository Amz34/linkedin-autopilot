#!/usr/bin/env python3
"""
LinkedIn Post Tool — post to personal profile or company page.
Content: manual text OR AI-generated (DeepSeek). Images supported.

Usage:
  python post.py --personal "Your text here"
  python post.py --personal "Your text here" --image photo.jpg
  python post.py --page "Your text here"
  python post.py --ai --personal [--topic "facility management"]
  python post.py --ai --page [--topic "cleaning services"]
"""
import argparse
import json
import os
import sys
import time
from urllib.parse import urlencode
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE, ".env")
TOKEN_PATH = os.path.join(BASE, "token.json")
REDIRECT = "http://localhost:8787/callback"

# Known company pages (add more as needed)
PAGES = {
    "luxewave": "urn:li:organization:115792525",
    "ifmi": "urn:li:organization:108790715",
}

AI_SYSTEM = """You are a LinkedIn content writer for IFMI — International Facilities Management Insights, a Saudi Arabia facility-management company page. Write engaging, professional LinkedIn posts in the same language as the user's request (English or Arabic). Rules:
- Hook in the first line, value in the middle, ALWAYS end with a clear CTA inviting likes, comments, shares, and follows (e.g. "Like if...", "Comment...", "Share this with...", "Follow for more...")
- Use short lines and 2-4 emojis max, relevant hashtags at the end (3-5)
- 100-220 words, no clickbait, no fake stats
- Tone: credible, helpful, industry-insight
- NEVER use em dashes (—) or en dashes (–); use commas, colons, or periods instead
If the topic is about Luxe Wave (hospitality supply), write hospitality procurement content instead."""


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        for line in open(ENV_PATH, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def load_token():
    if not os.path.exists(TOKEN_PATH):
        print("❌ token.json nahi mila. Pehle chalao:  python auth.py")
        sys.exit(1)
    with open(TOKEN_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_token(token):
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token, f, indent=2)


def refresh_if_needed(token, env):
    expires_in = token.get("expires_in", 86400)
    obtained = token.get("obtained_at", 0)
    if time.time() - obtained < expires_in - 300:
        return token, False
    refresh = token.get("refresh_token")
    if not refresh:
        print("⚠️ Token expire hone wala hai aur refresh_token nahi hai. Dobara: python auth.py")
        return token, False
    print("🔄 Token refresh ho raha hai...")
    data = urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": env["LINKEDIN_CLIENT_ID"],
        "client_secret": env["LINKEDIN_CLIENT_SECRET"],
    }).encode()
    req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=data)
    with urllib.request.urlopen(req) as resp:
        new_token = json.loads(resp.read())
    new_token["obtained_at"] = time.time()
    save_token(new_token)
    return new_token, True


def api_json(method, url, headers=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}, dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        return e.code, json.loads(raw) if raw else {"error": str(e)}, {}


def generate_post(env, topic):
    """DeepSeek content generation."""
    key = env.get("DEEPSEEK_API_KEY", "")
    if not key:
        print("❌ .env mein DEEPSEEK_API_KEY nahi hai — AI mode ke liye zaroori.")
        sys.exit(1)
    model = env.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    prompt = f"Write a LinkedIn post about: {topic}" if topic else "Write a LinkedIn post about facility management insights for the Saudi market."
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": AI_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 700,
        "temperature": 0.8,
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def upload_image(token, author_urn, image_path):
    """Register + upload image via modern Images API, return image URN."""
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202601",
    }
    body = {
        "initializeUploadRequest": {
            "owner": author_urn,
        }
    }
    status, data, _ = api_json("POST", "https://api.linkedin.com/rest/images?action=initializeUpload", headers, body)
    if status not in (200, 201):
        print(f"❌ Image register fail ({status}): {json.dumps(data, ensure_ascii=False)[:400]}")
        return None
    value = data.get("value", {})
    upload_url = value.get("uploadUrl")
    image_urn = value.get("image")
    if not upload_url or not image_urn:
        print("❌ Upload URL/image URN nahi mila:", json.dumps(data, ensure_ascii=False)[:400])
        return None
    with open(image_path, "rb") as f:
        img_data = f.read()
    req = urllib.request.Request(
        upload_url,
        data=img_data,
        headers={"Authorization": f"Bearer {token['access_token']}", "Content-Type": "application/octet-stream"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            resp.read()
        print("✅ Image upload ho gaya")
    except urllib.error.HTTPError as e:
        print(f"❌ Image upload fail ({e.code}): {e.read().decode('utf-8', 'replace')[:400]}")
        return None
    return image_urn


def post_share(token, author_urn, text, image_path=None):
    """Publish a post via modern Posts API. If image_path given, upload image first."""
    media_category = "NONE"
    if image_path:
        print(f"🖼️ Image upload ho raha hai ({os.path.basename(image_path)})...")
        image_urn = upload_image(token, author_urn, image_path)
        if image_urn:
            media_category = "IMAGE"
        else:
            print("⚠️ Image upload fail — bina image ke text post karta hoon.")

    body = {
        "author": author_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if media_category == "IMAGE":
        body["content"] = {
            "media": {
                "id": image_urn,
                "altText": text[:200],
            }
        }
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202601",
    }
    status, data, resp_headers = api_json("POST", "https://api.linkedin.com/rest/posts", headers, body)
    if status in (200, 201):
        # new API returns post URN in Location header
        post_id = data.get("id", "") if data else ""
        if not post_id:
            loc = resp_headers.get("Location", "")
            post_id = loc.rstrip("/").rsplit("/", 1)[-1].replace("urn:li:share:", "")
        print(f"✅ Post published! ID: {post_id}")
        print(f"   LinkedIn pe dekh lo — post URN: urn:li:share:{post_id}")
        return True
    print(f"❌ Post fail ({status}): {json.dumps(data, ensure_ascii=False)[:500]}")
    return False


def main():
    parser = argparse.ArgumentParser(description="LinkedIn post tool")
    parser.add_argument("--personal", action="store_true", help="Post to personal profile")
    parser.add_argument("--page", action="store_true", help="Post to company page")
    parser.add_argument("--page-name", default="", help="Page name: luxewave (or ifmi)")
    parser.add_argument("--org-urn", default="", help="Direct org URN (override)")
    parser.add_argument("--ai", action="store_true", help="Generate content with AI (DeepSeek)")
    parser.add_argument("--topic", default="", help="Topic for AI-generated post")
    parser.add_argument("--image", default="", help="Image file path (jpg/png/webp/gif)")
    parser.add_argument("text", nargs="?", default="", help="Manual post text")
    args = parser.parse_args()

    if not args.personal and not args.page:
        print("❌ --personal ya --page choose karo.")
        sys.exit(1)

    env = load_env()
    token = load_token()
    token, refreshed = refresh_if_needed(token, env)

    if args.ai:
        text = generate_post(env, args.topic)
        print("🤖 AI post generated:\n")
        print("---")
        print(text)
        print("---\n")
    else:
        text = args.text.strip()
        if not text:
            print("❌ Manual mode mein text do:  python post.py --personal \"text\"")
            sys.exit(1)

    if args.image and not os.path.exists(args.image):
        print(f"❌ Image file nahi mili: {args.image}")
        sys.exit(1)

    if args.personal:
        # person URN from userinfo sub
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        status, info, _ = api_json("GET", "https://api.linkedin.com/v2/userinfo", headers)
        if status != 200 or "sub" not in info:
            print("❌ Profile info nahi mili:", status, info)
            sys.exit(1)
        author = f"urn:li:person:{info['sub']}"
        print(f"👤 Posting to personal profile...")
        ok = post_share(token, author, text, args.image or None)
    else:
        # company page post — use known PAGES or --org-urn (org-list API needs Community Mgmt API)
        if args.org_urn:
            author = args.org_urn
        elif args.page_name and args.page_name.lower() in PAGES:
            author = PAGES[args.page_name.lower()]
        elif len(PAGES) == 1:
            author = list(PAGES.values())[0]
        else:
            print("🏢 Known pages:")
            for i, (name, urn) in enumerate(PAGES.items(), 1):
                print(f"   {i}. {name} — {urn}")
            choice = input("Kaunsa page? (name): ").strip().lower()
            if choice not in PAGES:
                print("❌ Unknown page:", choice)
                sys.exit(1)
            author = PAGES[choice]
        print(f"📣 Posting to {author} ...")
        ok = post_share(token, author, text, args.image or None)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
