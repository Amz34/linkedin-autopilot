#!/usr/bin/env python3
"""
LinkedIn OAuth — authorize + save token (with refresh support).
Run once:  python auth.py
"""
import json
import os
import sys
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE, ".env")
TOKEN_PATH = os.path.join(BASE, "token.json")
PORT = 8787
REDIRECT = f"http://localhost:{PORT}/callback"
SCOPES = "openid profile email w_member_social"


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        for line in open(ENV_PATH, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/callback"):
            qs = parse_qs(urlparse(self.path).query)
            code = qs.get("code", [None])[0]
            self.server.auth_code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if code:
                msg = "<h2 style='font-family:sans-serif'>✅ Success! Token saved. You can close this window.</h2>"
            else:
                msg = "<h2 style='font-family:sans-serif'>❌ No code received. Close this window and try again.</h2>"
            self.wfile.write(msg.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


def api_post(url, data, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    env = load_env()
    client_id = env.get("LINKEDIN_CLIENT_ID", "")
    client_secret = env.get("LINKEDIN_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("❌ LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET not found in .env.")
        print("   Create the .env file first (see README) and re-run.")
        sys.exit(1)

    auth_url = "https://www.linkedin.com/oauth/v2/authorization?" + urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
        "state": "linkedin_tool_local",
    })

    print("Opening browser... authorize on LinkedIn.")
    print("If the browser did not open, open this URL yourself:\n")
    print(f"   {auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    server.auth_code = None
    server.handle_request()  # wait for the single callback
    code = server.auth_code

    if not code:
        print("❌ Authorization code not received. Try again.")
        sys.exit(1)

    # Exchange code -> access token + refresh token
    data = urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT,
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()
    try:
        token = api_post("https://www.linkedin.com/oauth/v2/accessToken", data)
    except Exception as e:
        print("❌ Token exchange failed:", e)
        sys.exit(1)

    token["obtained_at"] = time.time()
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token, f, indent=2)
    print("✅ Access token saved → token.json")

    # Profile info (OpenID Connect userinfo)
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    try:
        info = api_get("https://api.linkedin.com/v2/userinfo", headers)
        person_id = info.get("sub", "")
        print(f"👤 Logged in as: {info.get('name', '?')} (person URN: urn:li:person:{person_id})")
    except Exception as e:
        print("⚠️ Profile info fetch failed (ignore if not needed):", e)

    # Organizations user administers
    try:
        acls = api_get(
            "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee&role=ADMINISTRATOR",
            headers,
        )
        orgs = []
        for e in acls.get("elements", []):
            urn = e.get("organizationalTarget", "")
            if urn:
                orgs.append(urn)
        if orgs:
            print(f"🏢 Admin pages ({len(orgs)}):")
            for o in orgs:
                print(f"   - {o}")
        else:
            print("🏢 No organization admin list found (Community Management API is needed for page posts).")
    except Exception as e:
        print("⚠️ Organization list fetch failed:", e)

    print("\n🎉 Auth complete! Now use post.py:")
    print("   python post.py --personal \"text\"")
    print("   python post.py --page \"text\"")
    print("   python post.py --ai --personal")


if __name__ == "__main__":
    main()
