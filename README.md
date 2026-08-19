# LinkedIn Post Tool — IFMI / Luxe Wave

LinkedIn pe post karne ka local tool — personal profile aur company pages dono pe.
Content manual likho ya AI (DeepSeek) se generate karo.

## Setup (ek baar, 10 minute)

### 1. LinkedIn Developer App banao
1. https://developer.linkedin.com → **My Apps** → **Create app**
   - App name: `IFMI Content Tool`
   - LinkedIn Page: apni koi bhi page (ya personal) — baad mein change hota hai
   - Logo: koi bhi image
2. **Products** tab → ye teeno add karo:
   - ✅ **Sign In with LinkedIn using OpenID Connect**
   - ✅ **Share on LinkedIn**
   - ✅ **Community Management API**
3. **Auth** tab → **Redirect URLs** mein ye daalo:
   ```
   http://localhost:8787/callback
   ```
4. **Credentials** tab → **Client ID** aur **Client Secret** copy karo

### 2. .env file banao
```
copy .env.example .env
```
phir `.env` mein values daalo:
- `LINKEDIN_CLIENT_ID` = Client ID
- `LINKEDIN_CLIENT_SECRET` = Client Secret
- `DEEPSEEK_API_KEY` = aapki DeepSeek key (AI mode ke liye)

### 3. Authorize karo
```
python auth.py
```
Browser khulega → LinkedIn pe **Allow** dabao → token save ho jayega.

## Use

```bash
# Manual post — personal profile
python post.py --personal "Hello LinkedIn! ..."

# Manual post with image — personal profile
python post.py --personal "Hello LinkedIn! ..." --image photo.jpg

# Manual post — company page
python post.py --page "Hello! ..."

# AI post — personal (topic optional)
python post.py --ai --personal --topic "facility management trends"

# AI post — company page
python post.py --ai --page --topic "cleaning services KSA"
```

## Image posts

```bash
# Text + image (jpg/png/webp/gif) — personal profile
python post.py --personal "Your text" --image banner.png

# AI post + image
python post.py --ai --personal --image banner.png

# Apna banner banao (Python PIL):
python make_banner.py   # -> banner.png
```

## Files
| File | Kaam |
|---|---|
| `auth.py` | LinkedIn login + token save/refresh |
| `post.py` | Post karna (manual + AI) |
| `.env` | Credentials (KABHI share mat karo) |
| `token.json` | Access token (auto-refresh hota hai) |

## Security
- `.env` aur `token.json` **kabhi GitHub/chat mein mat bhejo**
- Token LinkedIn ke andar revoke kar sakte ho (Settings → Data privacy → Permissions)
