#!/usr/bin/env python3
"""Publish new CORE HTML stories. Standard library only."""
import base64
import hashlib
from html.parser import HTMLParser
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / ".github/social-published.json"
SITE = "https://core.iiankehn.com"
PLATFORMS = ("bluesky", "threads", "x")

class Article(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.image = ""
        self.in_h1 = False
        self.in_deck = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        if tag == "h1":
            self.in_h1 = True
        if tag == "p" and "article-deck" in a.get("class", "").split():
            self.in_deck = True
        if tag == "img" and not self.image:
            self.image = a.get("src", "")
    def handle_endtag(self, tag):
        if tag == "h1": self.in_h1 = False
        if tag == "p": self.in_deck = False
    def handle_data(self, data):
        if self.in_h1: self.title += data
        if self.in_deck: self.description = self.description or data

def request(url, data=None, headers=None, method=None):
    payload = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    req = Request(url, data=payload, headers=headers or {}, method=method)
    if isinstance(data, (dict, list)):
        req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=35) as res:
        body = res.read()
        return json.loads(body) if body else {}

def env(*names):
    vals = [os.getenv(n, "") for n in names]
    return vals if all(vals) else None

def bluesky(article, url):
    creds = env("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD")
    if not creds: return None
    base = "https://bsky.social/xrpc/"
    session = request(base+"com.atproto.server.createSession", dict(identifier=creds[0], password=creds[1]))
    auth = {"Authorization": "Bearer "+session["accessJwt"]}
    text = article.title + "\n\n" + url
    if len(text) > 300: text = article.title[:250] + "…\n" + url
    start = len(text.encode("utf-8"))-len(url.encode("utf-8"))
    record = {"$type":"app.bsky.feed.post","text":text,"createdAt":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"facets":[{"index":{"byteStart":start,"byteEnd":len(text.encode("utf-8"))},"features":[{"$type":"app.bsky.richtext.facet#link","uri":url}]}]}
    image = article.image
    thumb = None
    if image:
        image_url = SITE + "/assets/images/" + Path(image).name
        try:
            binary = request(image_url)
        except Exception:
            try:
                with urlopen(image_url,timeout=20) as r: binary = r.read()
                upload = request(base+"com.atproto.repo.uploadBlob", binary, {**auth,"Content-Type":"image/webp"})
                thumb = upload["blob"]
            except Exception as exc:
                print("Bluesky thumbnail unavailable:",exc)
    external = {"uri":url,"title":article.title,"description":article.description[:300]}
    if thumb: external["thumb"] = thumb
    record["embed"] = {"$type":"app.bsky.embed.external","external":external}
    return request(base+"com.atproto.repo.createRecord",{"repo":session["did"],"collection":"app.bsky.feed.post","record":record},auth)

def threads(article,url):
    creds = env("THREADS_USER_ID","THREADS_ACCESS_TOKEN")
    if not creds: return None
    uid, token = creds
    base = "https://graph.threads.net/v1.0/"
    text = (article.title + "\n\n" + article.description + "\n\n" + url)[:500]
    params = {"media_type":"TEXT","text":text,"access_token":token}
    container = request(base+quote(uid)+"/threads?"+urlencode(params),data=b"",method="POST")
    time.sleep(3)
    return request(base+quote(uid)+"/threads_publish?"+urlencode({"creation_id":container["id"],"access_token":token}),data=b"",method="POST")

def x_post(article,url):
    creds = env("X_API_KEY","X_API_SECRET","X_ACCESS_TOKEN","X_ACCESS_TOKEN_SECRET")
    if not creds: return None
    key,secret,token,token_secret = creds
    endpoint = "https://api.x.com/2/tweets"
    message = article.title[:220] + "\n\n" + url
    oauth = {"oauth_consumer_key":key,"oauth_nonce":secrets.token_hex(16),"oauth_signature_method":"HMAC-SHA1","oauth_timestamp":str(int(time.time())),"oauth_token":token,"oauth_version":"1.0"}
    def enc(s): return quote(str(s),safe="~-._")
    param = "&".join(enc(k)+"="+enc(v) for k,v in sorted(oauth.items()))
    base = "&".join([enc("POST"),enc(endpoint),enc(param)])
    signature = base64.b64encode(hmac.new((enc(secret)+"&"+enc(token_secret)).encode(),base.encode(),hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = signature
    header = "OAuth "+", ".join(enc(k)+'="'+enc(v)+'"' for k,v in sorted(oauth.items()))
    return request(endpoint,{"text":message},{"Authorization":header})

def main():
    dry = os.getenv("DRY_RUN","false").lower() == "true"
    if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch":
        candidates = sorted((ROOT/"posts").glob("*.html"))
    else:
        before = os.getenv("GITHUB_EVENT_BEFORE","")
        after = os.getenv("GITHUB_SHA","HEAD")
        if not before or set(before)=={"0"}:
            print("No usable base commit; skipping automatic backfill.")
            return
        changed = subprocess.check_output(["git","diff","--name-only","--diff-filter=A",before,after,"--","posts/"],cwd=ROOT,text=True).splitlines()
        candidates = [ROOT/p for p in changed if p.endswith(".html")]
    ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    failed = False
    for path in candidates:
        if not path.is_file(): continue
        rel = path.relative_to(ROOT).as_posix()
        article = Article()
        article.feed(path.read_text(encoding="utf-8"))
        if not article.title: continue
        url = SITE+"/"+rel
        ledger.setdefault(rel,{})
        for platform, publish in [("bluesky",bluesky),("threads",threads),("x",x_post)]:
            if ledger[rel].get(platform): continue
            if dry:
                print("PREVIEW",platform,article.title,url)
                continue
            try:
                result = publish(article,url)
                if result is None:
                    print("Not configured:",platform)
                    continue
                ledger[rel][platform] = result.get("uri") or result.get("id") or result.get("data",{}).get("id") or "published"
                LEDGER.parent.mkdir(parents=True,exist_ok=True)
                LEDGER.write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n")
                print("Published:",platform,rel)
            except Exception as exc:
                failed = True
                print("ERROR:",platform,rel,str(exc),file=sys.stderr)
    if failed: sys.exit(1)

if __name__ == "__main__": main()
