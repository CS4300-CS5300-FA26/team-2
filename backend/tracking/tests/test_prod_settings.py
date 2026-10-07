import os
import subprocess
import sys

from django.test import SimpleTestCase


class ProdEmailSettingsTests(SimpleTestCase):
    """Prod must boot without email config (falling back to logging emails),
    and use SMTP when it is configured."""

    def _prod_email_backend(self, env_overrides, unset=()):
        env = {**os.environ, "SECRET_KEY": "test", **env_overrides}
        for key in unset:
            env.pop(key, None)
        result = subprocess.run(
            [sys.executable, "-c", "import pathfinder.settings.prod as s; print(s.EMAIL_BACKEND)"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_missing_email_config_falls_back_to_console(self):
        result = self._prod_email_backend(
            {}, unset=("EMAIL_HOST", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD", "DEFAULT_FROM_EMAIL")
        )
        self.assertIn("console.EmailBackend", result.stdout)
        self.assertIn("EMAIL_HOST is not set", result.stderr)

    def test_full_email_config_uses_smtp(self):
        result = self._prod_email_backend({
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_HOST_USER": "u",
            "EMAIL_HOST_PASSWORD": "p",
        })
        self.assertIn("smtp.EmailBackend", result.stdout)
