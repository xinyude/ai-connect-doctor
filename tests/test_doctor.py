import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from ai_connect_doctor.__main__ import diagnose


class DoctorTests(unittest.TestCase):
    def run_doctor(self, **variables):
        env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
        env.update(variables)
        return subprocess.run([sys.executable, '-m', 'ai_connect_doctor', '--json'],
                              env=env, text=True, capture_output=True, check=True)

    def test_report_never_exposes_proxy_credentials_or_hosts(self):
        report = self.run_doctor(HTTPS_PROXY='http://alice:secret@private.example:8080',
                                 NO_PROXY='localhost,[::1]')
        self.assertNotIn('secret', report.stdout)
        self.assertNotIn('private.example', report.stdout)
        self.assertNotIn('alice', report.stdout)
        data = json.loads(report.stdout)
        self.assertTrue(any(x['id'] == 'proxy.https_proxy' for x in data['checks']))

    def test_flags_bracketed_ipv6_no_proxy(self):
        data = json.loads(self.run_doctor(NO_PROXY='localhost,[::1]').stdout)
        self.assertTrue(any(x['id'] == 'proxy.no_proxy_ipv6' and x['status'] == 'warning'
                            for x in data['checks']))

    def test_normal_no_proxy_is_not_flagged(self):
        data = json.loads(self.run_doctor(NO_PROXY='localhost,127.0.0.1,::1').stdout)
        self.assertFalse(any(x['id'] == 'proxy.no_proxy_ipv6' for x in data['checks']))

    def test_rejects_http_target_without_connecting(self):
        result = subprocess.run([sys.executable, '-m', 'ai_connect_doctor', '--url', 'http://example.com'], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('https', result.stderr.lower())

    def test_rejects_url_with_credentials_and_does_not_echo_them(self):
        result = subprocess.run([sys.executable, '-m', 'ai_connect_doctor', '--url', 'https://alice:secret@example.com'], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('secret', result.stderr + result.stdout)

    def test_https_error_response_proves_reachability_only(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=HTTPError('https://example.com', 401, 'unauthorized', {}, None)):
            checks = diagnose(url='https://example.com')['checks']
        result = next(x for x in checks if x['id'] == 'network.https')
        self.assertEqual(result['status'], 'ok')
        self.assertIn('does not verify API access', result['message'])

    def test_https_connection_failure_is_reported_without_details(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=URLError('private secret')):
            checks = diagnose(url='https://example.com')['checks']
        result = next(x for x in checks if x['id'] == 'network.https')
        self.assertEqual(result['status'], 'warning')
        self.assertNotIn('secret', result['message'])


if __name__ == '__main__':
    unittest.main()
