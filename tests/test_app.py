import unittest

from app import app, extract_share_url, validate_image_url, validate_note_url


class UrlValidationTests(unittest.TestCase):
    def test_note_url(self):
        url = "https://www.xiaohongshu.com/explore/example-note"
        self.assertEqual(validate_note_url(url), url)

    def test_short_share_url(self):
        url = "https://xhslink.com/abc123"
        self.assertEqual(extract_share_url(f"复制这条内容，打开小红书查看：{url}"), url)

    def test_reject_untrusted_note_host(self):
        with self.assertRaises(ValueError):
            validate_note_url("https://example.com/note")

    def test_reject_untrusted_image_host(self):
        with self.assertRaises(ValueError):
            validate_image_url("http://127.0.0.1/private")

    def test_reject_non_http_scheme(self):
        with self.assertRaises(ValueError):
            validate_note_url("file:///etc/passwd")


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    def test_analyze_rejects_untrusted_url(self):
        response = self.client.post("/api/analyze", json={"url": "https://example.com/"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
