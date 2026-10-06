import os
import subprocess
import sys

from django.test import SimpleTestCase


class ProdEmailSettingsTests(SimpleTestCase):
    """Prod settings must fail to import without email config, not silently
    fall back to Django's default SMTP-to-nowhere backend."""

    def _import_prod_settings(self, env_overrides, unset=()):
        env = {**os.environ, **env_overrides}
        for key in unset:
            env.pop(key, None)
        result = subprocess.run(
            [sys.executable, "-c", "import pathfinder.settings.prod"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            env=env,
            capture_output=True,
            text=True,
        )
        return result

    def test_missing_email_host_raises(self):
        result = self._import_prod_settings(
            {"SECRET_KEY": "test", "EMAIL_HOST_USER": "u", "EMAIL_HOST_PASSWORD": "p"},
            unset=("EMAIL_HOST",),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EMAIL_HOST", result.stderr)

    def test_full_email_config_imports_cleanly(self):
        result = self._import_prod_settings({
            "SECRET_KEY": "test",
            "EMAIL_HOST": "smtp.example.com",
            "EMAIL_HOST_USER": "u",
            "EMAIL_HOST_PASSWORD": "p",
        })
        self.assertEqual(result.returncode, 0, result.stderr)
