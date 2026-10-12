from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Resume


MAX_RESUME_SIZE = 5 * 1024 * 1024


class ResumeUploadTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()

        self.user = self.create_user("resume-owner")
        self.url = reverse("resumes:upload")

    def tearDown(self):
        self.settings_override.disable()
        self.media_dir.cleanup()
        super().tearDown()

    def create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            password="test-password-123",
        )

    def sign_in(self):
        self.client.force_login(self.user)

    def post_upload(self, filename, content, content_type, follow=False):
        uploaded_file = SimpleUploadedFile(
            filename,
            content,
            content_type=content_type,
        )
        return self.client.post(self.url, {"file": uploaded_file}, follow=follow)

    def test_upload_page_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_pdf_upload_sets_the_logged_in_user_as_owner(self):
        self.sign_in()

        response = self.post_upload(
            "resume.pdf",
            b"%PDF-1.4 test file",
            "application/pdf",
            follow=True,
        )

        resume = Resume.objects.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resume.owner, self.user)
        self.assertContains(response, "resume.pdf")

    def test_invalid_uploads_are_rejected_and_not_saved(self):
        self.sign_in()

        invalid_uploads = (
            ("not-a-resume.txt", b"This should be rejected", "text/plain"),
            (
                "large-resume.pdf",
                b"x" * (MAX_RESUME_SIZE + 1),
                "application/pdf",
            ),
        )

        for filename, content, content_type in invalid_uploads:
            with self.subTest(filename=filename):
                response = self.post_upload(filename, content, content_type)

                self.assertEqual(response.status_code, 200)
                self.assertIn("file", response.context["form"].errors)
                self.assertFalse(Resume.objects.exists())

    def test_user_cannot_see_another_users_resume(self):
        other_user = self.create_user("other-user")
        Resume.objects.create(
            owner=other_user,
            file=SimpleUploadedFile(
                "private-resume.pdf",
                b"%PDF-1.4 private file",
                content_type="application/pdf",
            ),
        )

        self.sign_in()
        response = self.client.get(self.url)

        self.assertNotContains(response, "private-resume.pdf")