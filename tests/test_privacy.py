import unittest
from app.privacy import sanitize_text


class PrivacyTests(unittest.TestCase):
    def test_redacts_private_ip(self):
        self.assertEqual(sanitize_text("Connection from 10.20.100.252"), "Connection from <INTERNAL_IP>")
        self.assertEqual(sanitize_text("Src 192.168.1.50 dst 172.16.5.2"), "Src <INTERNAL_IP> dst <INTERNAL_IP>")

    def test_redacts_public_ip(self):
        self.assertEqual(sanitize_text("Attacker at 195.201.245.94"), "Attacker at <EXTERNAL_IP>")

    def test_redacts_localhost(self):
        self.assertEqual(sanitize_text("Service at 127.0.0.1"), "Service at <LOCALHOST>")

    def test_redacts_passwords_and_tokens(self):
        s = "POST /api/login password=MySecret123 token=abc_987654321 auth:Bearer_XYZ"
        res = sanitize_text(s)
        self.assertNotIn("MySecret123", res)
        self.assertNotIn("abc_987654321", res)
        self.assertIn("password=<REDACTED_SECRET>", res)
        self.assertIn("token=<REDACTED_SECRET>", res)

    def test_redacts_emails(self):
        s = "Alert sent to admin.soc@company.corp by analyst@domain.com"
        res = sanitize_text(s)
        self.assertNotIn("admin.soc@company.corp", res)
        self.assertNotIn("analyst@domain.com", res)
        self.assertIn("<REDACTED_EMAIL>", res)


if __name__ == "__main__":
    unittest.main()
