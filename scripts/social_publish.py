#!/usr/bin/env python3
"""CORE social clients. Safe by default; no automatic backfill or POST retries."""
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
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / '.github/social-published.json'
SITE = 'https://core.iiankehn.com'
PLATFORMS = ('bluesky', 'threads', 'x')
KEYS = {
    'bluesky': ('BLUESKY_HANDLE', 'BLUESKY_APP_PASSWORD'),
    'threads': ('THREADS_USER_ID', 'THREADS_ACCESS_TOKEN'),
    'x': ('X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET'),
}

class Article(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = self.description = ''
        self.in_h1 = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name') == 'description':
            self.description = attrs.get('content', '')
        if tag == 'h1': self.in_h1 = True
    def handle_endtag(self, tag):
        if tag == 'h1': self.in_h1 = False
    def handle_data(self, data):
        if self.in_h1: self.title += data

class APIError(RuntimeError):
    pass

class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError('API redirect refused')

def request(url, data=None, headers=None, method=None):
    # Tokens never appear in URLs or diagnostic output. Never retry a write.
    payload = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    req = Request(url, data=payload, headers=headers or {}, method=method)
    if isinstance(data, (dict, list)): req.add_header('Content-Type', 'application/json')
    try:
        with build_opener(NoRedirects).open(req, timeout=35) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise APIError(f'HTTP {exc.code}; check account permissions, expiry and API quota') from None
    except Exception:
        raise APIError('API response unavailable or invalid; reconcile before retrying writes') from None

def credentials(platform):
    values = [os.getenv(name, '') for name in KEYS[platform]]
    if not all(values): raise APIError('Missing configuration: ' + ', '.join(KEYS[platform]))
    return values

def text_for(article, url, platform):
    # Conservative budgets handle Unicode without splitting encoded characters.
    # X reserves 23 weighted characters for t.co; each title character costs <= 2.
    title = ' '.join(article.title.split())
    if platform == 'x': return title[:120] + '\n\n' + url
    budget = (300 if platform == 'bluesky' else 500) - len(('\n\n' + url).encode())
    if budget < 4: raise ValueError('Article URL exceeds text budget')
    title = title.encode()[:budget].decode('utf-8', errors='ignore')
    return title + '\n\n' + url

def bsky_session():
    handle, password = credentials('bluesky')
    return request('https://bsky.social/xrpc/com.atproto.server.createSession',
                   {'identifier': handle, 'password': password})

def bluesky(article, url):
    session = bsky_session()
    text = text_for(article, url, 'bluesky')
    end = len(text.encode())
    record = {'$type': 'app.bsky.feed.post', 'text': text,
              'createdAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'facets': [{'index': {'byteStart': end-len(url.encode()), 'byteEnd': end},
                          'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': url}]}],
              'embed': {'$type': 'app.bsky.embed.external', 'external': {
                  'uri': url, 'title': article.title, 'description': article.description[:300]}}}
    result = request('https://bsky.social/xrpc/com.atproto.repo.createRecord',
                     {'repo': session['did'], 'collection': 'app.bsky.feed.post', 'record': record},
                     {'Authorization': 'Bearer ' + session['accessJwt']})
    return result['uri']

def threads(article, url):
    uid, token = credentials('threads')
    base = 'https://graph.threads.net/v1.0/'
    auth = {'Authorization': 'Bearer ' + token}
    form = urlencode({'media_type': 'TEXT', 'text': text_for(article, url, 'threads')}).encode()
    container = request(base+quote(uid, safe='')+'/threads', form,
                        {**auth, 'Content-Type': 'application/x-www-form-urlencoded'}, 'POST')['id']
    for _ in range(10):
        status = request(base+quote(container, safe='')+'?fields=status,error_message', headers=auth)
        if status.get('status') == 'FINISHED': break
        if status.get('status') in ('ERROR', 'EXPIRED'): raise APIError('Threads container failed')
        time.sleep(2)
    else: raise APIError('Threads container not ready; reconcile before retry')
    return request(base+quote(uid, safe='')+'/threads_publish',
                   urlencode({'creation_id': container}).encode(),
                   {**auth, 'Content-Type': 'application/x-www-form-urlencoded'}, 'POST')['id']

def x_auth(method, endpoint):
    key, secret, token, token_secret = credentials('x')
    enc = lambda value: quote(str(value), safe='~-._')
    oauth = {'oauth_consumer_key': key, 'oauth_nonce': secrets.token_hex(16),
             'oauth_signature_method': 'HMAC-SHA1', 'oauth_timestamp': str(int(time.time())),
             'oauth_token': token, 'oauth_version': '1.0'}
    params = '&'.join(enc(k)+'='+enc(v) for k,v in sorted(oauth.items()))
    signature_base = '&'.join(map(enc, (method, endpoint, params)))
    oauth['oauth_signature'] = base64.b64encode(hmac.new(
        (enc(secret)+'&'+enc(token_secret)).encode(), signature_base.encode(), hashlib.sha1).digest()).decode()
    return {'Authorization': 'OAuth '+', '.join(enc(k)+'="'+enc(v)+'"' for k,v in sorted(oauth.items()))}

def x_post(article, url):
    endpoint = 'https://api.x.com/2/tweets'
    return request(endpoint, {'text': text_for(article, url, 'x')}, x_auth('POST', endpoint))['data']['id']

def validate(platform):
    if platform == 'bluesky':
        session = bsky_session()
        result = request('https://bsky.social/xrpc/com.atproto.server.getSession',
                         headers={'Authorization': 'Bearer '+session['accessJwt']})
        return result['handle']
    if platform == 'threads':
        uid, token = credentials(platform)
        result = request('https://graph.threads.net/v1.0/me?fields=id,username',
                         headers={'Authorization': 'Bearer '+token})
        if str(result['id']) != uid: raise APIError('Threads account ID mismatch')
        return result['username']
    endpoint = 'https://api.x.com/2/users/me'
    return request(endpoint, headers=x_auth('GET', endpoint))['data']['username']

def save(ledger):
    temporary = LEDGER.with_suffix('.tmp')
    temporary.write_text(json.dumps(ledger, indent=2, sort_keys=True)+'\n')
    temporary.replace(LEDGER)
    if os.getenv('LEDGER_COMMIT') == 'true':
        # Persist intent BEFORE sending, success AFTER. Unknown writes never auto-retry.
        for args in (['add', '.github/social-published.json'],
                     ['commit', '-m', 'chore: persist social publishing state [skip ci]'],
                     ['push', 'origin', 'HEAD:main']):
            subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True)

def publish_once(ledger, key, platform, article, url):
    if platform in ledger.get(key, {}):
        print('Already recorded or needs reconciliation:', platform, key)
        return
    credentials(platform)
    ledger.setdefault(key, {})[platform] = {'status': 'pending'}
    save(ledger)
    try:
        identifier = {'bluesky': bluesky, 'threads': threads, 'x': x_post}[platform](article, url)
        ledger[key][platform] = {'status': 'published', 'id': identifier}
        save(ledger)
        print('Published:', platform, key)
    except Exception:
        # Pending is durable even if process terminates mid-request.
        raise APIError('Write incomplete; check platform and pending ledger before retrying') from None

def candidates():
    # Dispatch never scans history. Only added files from the push event qualify.
    if os.getenv('GITHUB_EVENT_NAME') != 'push': return []
    before, after = os.getenv('GITHUB_EVENT_BEFORE', ''), os.getenv('GITHUB_SHA', '')
    if not before or set(before) == {'0'} or not after: return []
    baseline = json.loads((ROOT/'.github/social-baseline.json').read_text())
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=A',
                                      before, after, '--', 'posts/'], cwd=ROOT, text=True).splitlines()
    return [ROOT/p for p in changed if p.startswith('posts/') and p.endswith('.html')
            and len(Path(p).parts) == 2 and p not in baseline and (ROOT/p).is_file()]

def main():
    mode = os.getenv('SOCIAL_MODE', 'preview')
    if mode == 'validate':
        failed = False
        for platform in PLATFORMS:
            try: print('Authenticated:', platform, validate(platform))
            except APIError as exc:
                print('Validation failed:', platform, str(exc), file=sys.stderr)
                failed = True
        if failed: raise SystemExit(1)
        print('Authentication passed. Write permissions still require a labeled test post.')
        return
    if mode not in ('preview', 'publish', 'test'): raise ValueError('Unknown social mode')
    ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
    if mode == 'test':
        platform = os.getenv('TEST_PLATFORM', '')
        test_id = os.getenv('TEST_ID', '')
        if platform not in PLATFORMS or not test_id.isalnum() or len(test_id) > 40:
            raise ValueError('Test requires one platform and an alphanumeric test ID (1-40 chars)')
        article = Article()
        article.title = f'CORE social publishing integration test ({test_id})'
        article.description = 'Temporary integration test; no existing article is being shared.'
        publish_once(ledger, 'test:'+test_id, platform, article, SITE)
        return
    if mode == 'publish' and (os.getenv('SOCIAL_PUBLISH_ENABLED') != 'true'
                             or os.getenv('GITHUB_REF') != 'refs/heads/main'
                             or os.getenv('GITHUB_EVENT_NAME') != 'push'):
        raise APIError('Live publishing is disabled or event is not a main push')
    if mode == 'publish':
        activation = os.getenv('SOCIAL_ACTIVATION_SHA', '')
        before = os.getenv('GITHUB_EVENT_BEFORE', '')
        if not activation or not before:
            raise APIError('Activation commit is required')
        subprocess.run(['git', 'merge-base', '--is-ancestor', activation, before],
                       cwd=ROOT, check=True, capture_output=True)
        for platform in PLATFORMS:
            if not any(key.startswith('test:') and value.get(platform, {}).get('status') == 'published'
                       for key, value in ledger.items()):
                raise APIError('All platforms must pass a labeled publication test before activation')
            validate(platform)
    failed = False
    for path in candidates():
        article = Article()
        article.feed(path.read_text())
        if not article.title.strip(): raise ValueError('Article has no title')
        rel = path.relative_to(ROOT).as_posix()
        url = SITE+'/'+rel
        for platform in PLATFORMS:
            if mode == 'preview': print('PREVIEW', platform, text_for(article, url, platform))
            else:
                try: publish_once(ledger, rel, platform, article, url)
                except APIError as exc:
                    failed = True
                    print('ERROR:', platform, str(exc), file=sys.stderr)
    if failed: raise SystemExit(1)

if __name__ == '__main__':
    try: main()
    except (APIError, ValueError, KeyError, subprocess.CalledProcessError):
        print('Social operation failed safely; review configuration or reconcile pending state.', file=sys.stderr)
        raise SystemExit(1)
