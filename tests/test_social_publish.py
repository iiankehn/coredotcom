import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('social', Path(__file__).resolve().parents[1]/'scripts/social_publish.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

class SocialTests(unittest.TestCase):
    def test_manual_never_backfills(self):
        with patch.dict(os.environ, {'GITHUB_EVENT_NAME': 'workflow_dispatch'}, clear=True):
            self.assertEqual(s.candidates(), [])
    def test_live_requires_gate_main_and_push(self):
        with patch.dict(os.environ, {'SOCIAL_MODE': 'publish'}, clear=True), patch.object(s, 'request') as req:
            with self.assertRaises(s.APIError): s.main()
            req.assert_not_called()
    def test_baseline_and_only_added(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root/'.github').mkdir()
            (root/'posts').mkdir()
            for name in ['old.html', 'new.html']: (root/'posts'/name).write_text('<h1>Article</h1>')
            (root/'.github/social-baseline.json').write_text('["posts/old.html"]')
            with patch.object(s,'ROOT',root), patch.dict(os.environ,{'GITHUB_EVENT_NAME':'push','GITHUB_EVENT_BEFORE':'abc','GITHUB_SHA':'def'}), patch.object(s.subprocess,'check_output',return_value='posts/old.html\nposts/new.html\nposts/deep/no.html\n') as diff:
                self.assertEqual(s.candidates(),[root/'posts/new.html'])
                self.assertIn('--diff-filter=A',diff.call_args.args[0])
    def test_text_keeps_full_url_and_unicode_limits(self):
        article = s.Article()
        article.title = '😀漢字é'*500
        url = s.SITE+'/posts/'+'a'*150+'.html'
        for platform, limit in [('bluesky',300),('threads',500)]:
            text = s.text_for(article,url,platform)
            self.assertTrue(text.endswith(url))
            self.assertLessEqual(len(text.encode()),limit)
        text = s.text_for(article,url,'x')
        self.assertLessEqual(len(text.split('\n')[0])*2+2+23,280)
    def test_metadata_parser(self):
        a=s.Article(); a.feed('<meta name="description" content="A &amp; B"><h1>Hello <em>world</em></h1>')
        self.assertEqual(a.title,'Hello world'); self.assertEqual(a.description,'A & B')
    def test_pending_saved_before_write_and_blocks_retry(self):
        ledger={}; states=[]
        def save(value): states.append(json.loads(json.dumps(value)))
        with patch.object(s,'credentials'), patch.object(s,'save',side_effect=save), patch.object(s,'x_post',side_effect=s.APIError('timeout')) as post:
            with self.assertRaises(s.APIError): s.publish_once(ledger,'post','x',s.Article(),s.SITE)
            self.assertEqual(states[0]['post']['x']['status'],'pending')
            s.publish_once(ledger,'post','x',s.Article(),s.SITE)
            self.assertEqual(post.call_count,1)
    def test_state_save_failure_prevents_write(self):
        with patch.object(s,'credentials'), patch.object(s,'save',side_effect=RuntimeError()), patch.object(s,'x_post') as post:
            with self.assertRaises(RuntimeError): s.publish_once({},'post','x',s.Article(),s.SITE)
            post.assert_not_called()
    def test_validate_makes_no_publication_calls(self):
        with patch.dict(os.environ,{'BLUESKY_HANDLE':'h','BLUESKY_APP_PASSWORD':'p','THREADS_USER_ID':'123','THREADS_ACCESS_TOKEN':'token','X_API_KEY':'k','X_API_SECRET':'s','X_ACCESS_TOKEN':'t','X_ACCESS_TOKEN_SECRET':'ts'}), patch.object(s,'request',side_effect=[{'did':'did:x','accessJwt':'jwt'},{'handle':'h'},{'id':'123','username':'u'},{'data':{'username':'u'}}]) as req:
            for platform in s.PLATFORMS: s.validate(platform)
            urls=[call.args[0] for call in req.call_args_list]
            self.assertFalse(any('createRecord' in url or 'threads_publish' in url or '/tweets' in url for url in urls))
            self.assertFalse(any('token' in url for url in urls))
    def test_threads_waits_for_container(self):
        with patch.object(s,'credentials',return_value=['id','secret']), patch.object(s.time,'sleep'), patch.object(s,'request',side_effect=[{'id':'container'},{'status':'IN_PROGRESS'},{'status':'FINISHED'},{'id':'post'}]) as req:
            a=s.Article(); a.title='Title'
            self.assertEqual(s.threads(a,s.SITE),'post')
            self.assertEqual(req.call_count,4)
            self.assertTrue(req.call_args.args[0].endswith('/threads_publish'))
    def test_activation_requires_success_on_every_platform(self):
        with patch.dict(os.environ, {'SOCIAL_MODE':'publish','SOCIAL_PUBLISH_ENABLED':'true','GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'push','SOCIAL_ACTIVATION_SHA':'abc','GITHUB_EVENT_BEFORE':'def'}, clear=True), patch.object(s.subprocess,'run'), patch.object(s,'validate') as validate:
            with self.assertRaises(s.APIError): s.main()
            validate.assert_not_called()
    def test_old_event_rejected_before_validation(self):
        with patch.dict(os.environ, {'SOCIAL_MODE':'publish','SOCIAL_PUBLISH_ENABLED':'true','GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'push','SOCIAL_ACTIVATION_SHA':'abc','GITHUB_EVENT_BEFORE':'def'}, clear=True), patch.object(s.subprocess,'run',side_effect=s.subprocess.CalledProcessError(1,['git'])), patch.object(s,'validate') as validate:
            with self.assertRaises(s.subprocess.CalledProcessError): s.main()
            validate.assert_not_called()
    def test_bluesky_link_facet_uses_utf8_bytes(self):
        a=s.Article(); a.title='Hello 😀'; url=s.SITE+'/posts/article.html'
        with patch.object(s,'bsky_session',return_value={'did':'did:x','accessJwt':'private'}), patch.object(s,'request',return_value={'uri':'at://post'}) as req:
            self.assertEqual(s.bluesky(a,url),'at://post')
            record=req.call_args.args[1]['record']
            index=record['facets'][0]['index']
            self.assertEqual(record['text'].encode()[index['byteStart']:index['byteEnd']].decode(),url)
    def test_failed_request_does_not_expose_credentials(self):
        from urllib.error import HTTPError
        with patch('urllib.request.OpenerDirector.open',side_effect=HTTPError('https://api.test?secret=value',401,'private-token',{},None)):
            with self.assertRaises(s.APIError) as error: s.request('https://api.test')
            self.assertNotIn('private-token',str(error.exception))
            self.assertNotIn('secret',str(error.exception))
    def test_sample_requires_explicit_platform_and_id(self):
        with patch.dict(os.environ,{'SOCIAL_MODE':'test'},clear=True), patch.object(s,'publish_once') as publish:
            with self.assertRaises(ValueError): s.main()
            publish.assert_not_called()

if __name__ == '__main__': unittest.main()
