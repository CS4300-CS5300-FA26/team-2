from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .services import (
    ResumeFeedbackError,
    create_file_data,
    get_resume_feedback,
)
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
            first_name="Test",
            last_name="User",
            email=f"{username}@example.com",
        )

    def sign_in(self):
        self.client.force_login(self.user)

    def create_resume(self, owner=None, filename="resume.pdf"):
        """
        Creates a resume that can be reused by feedback tests
        """

        return Resume.objects.create(
            owner=owner or self.user,
            file=SimpleUploadedFile(
                filename,
                b"%PDF-1.4 test file",
                content_type="application/pdf",
            ),
        )

    def post_upload(self, filename, content, content_type, follow=False):
        uploaded_file = SimpleUploadedFile(
            filename,
            content,
            content_type=content_type,
        )
        return self.client.post(self.url, {"file": uploaded_file}, follow=follow)

    def test_upload_page_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_pdf_upload_sets_the_logged_in_user_as_owner(self):
        self.sign_in()

        response = self.post_upload(
            "resume.pdf",
            b"%PDF-1.4 test file",
            "application/pdf",
        )

        resume = Resume.objects.get()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(resume.owner, self.user)
        self.assertTrue(response.json()["name"].startswith("resume"))
        listed = self.client.get(self.url).json()["results"]
        self.assertEqual([r["id"] for r in listed], [resume.id])

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

                self.assertEqual(response.status_code, 400)
                self.assertIn("file", response.json()["errors"])
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
    def test_user_can_delete_their_resume(self):
        resume = self.create_resume()

        stored_file_name = resume.file.name
        storage = resume.file.storage
        delete_url = reverse(
            "resumes:delete",
            args=[resume.id],
        )

        self.sign_in()

        self.assertTrue(
            storage.exists(stored_file_name)
        )

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Resume.objects.filter(id=resume.id).exists()
        )
        self.assertFalse(
            storage.exists(stored_file_name)
        )

        self.sign_in()
        response = self.client.get(self.url)

        self.assertEqual(response.json()["results"], [])
    def test_user_cannot_delete_another_users_resume(self):
        other_user = self.create_user("other-user")
        resume = self.create_resume(
            owner=other_user,
            filename="private-resume.pdf",
        )

        stored_file_name = resume.file.name
        storage = resume.file.storage
        delete_url = reverse(
            "resumes:delete",
            args=[resume.id],
        )

        self.sign_in()

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Resume.objects.filter(id=resume.id).exists()
        )
        self.assertTrue(
            storage.exists(stored_file_name)
        )

    def test_delete_requires_login(self):
        resume = self.create_resume()

        stored_file_name = resume.file.name
        storage = resume.file.storage
        delete_url = reverse(
            "resumes:delete",
            args=[resume.id],
        )

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            Resume.objects.filter(id=resume.id).exists()
        )
        self.assertTrue(
            storage.exists(stored_file_name)
        )

    def test_delete_requires_login(self):
        resume = self.create_resume()

        stored_file_name = resume.file.name
        storage = resume.file.storage
        delete_url = reverse(
            "resumes:delete",
            args=[resume.id],
        )

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 401)
        self.assertTrue(
            Resume.objects.filter(id=resume.id).exists()
        )
        self.assertTrue(
            storage.exists(stored_file_name)
        )

    def test_user_can_replace_their_resume(self):
        resume = self.create_resume()

        old_file_name = resume.file.name
        storage = resume.file.storage
        replace_url = reverse(
            "resumes:replace",
            args=[resume.id],
        )

        replacement_file = SimpleUploadedFile(
            "updated-resume.pdf",
            b"%PDF-1.4 updated resume",
            content_type="application/pdf",
        )

        self.sign_in()

        response = self.client.post(
            replace_url,
            {"file": replacement_file},
        )

        resume.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resume.owner, self.user)
        self.assertIn(
            "updated-resume",
            resume.file.name,
        )
        self.assertFalse(
            storage.exists(old_file_name)
        )
        self.assertTrue(
            storage.exists(resume.file.name)
        )

    def test_invalid_replacement_keeps_original_resume(self):
        resume = self.create_resume()

        old_file_name = resume.file.name
        storage = resume.file.storage
        replace_url = reverse(
            "resumes:replace",
            args=[resume.id],
        )

        invalid_file = SimpleUploadedFile(
            "not-a-resume.txt",
            b"This file should be rejected",
            content_type="text/plain",
        )

        self.sign_in()

        response = self.client.post(
            replace_url,
            {"file": invalid_file},
        )

        resume.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "file",
            response.json()["errors"],
        )
        self.assertEqual(
            resume.file.name,
            old_file_name,
        )
        self.assertTrue(
            storage.exists(old_file_name)
        )

    def test_user_cannot_replace_another_users_resume(self):
        other_user = self.create_user("replace-other-user")
        resume = self.create_resume(
            owner=other_user,
            filename="other-users-resume.pdf",
        )

        old_file_name = resume.file.name
        storage = resume.file.storage
        replace_url = reverse(
            "resumes:replace",
            args=[resume.id],
        )

        replacement_file = SimpleUploadedFile(
            "attempted-replacement.pdf",
            b"%PDF-1.4 replacement attempt",
            content_type="application/pdf",
        )

        self.sign_in()

        response = self.client.post(
            replace_url,
            {"file": replacement_file},
        )

        resume.refresh_from_db()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            resume.file.name,
            old_file_name,
        )
        self.assertTrue(
            storage.exists(old_file_name)
        )

    def test_replace_requires_login(self):
        resume = self.create_resume()

        old_file_name = resume.file.name
        storage = resume.file.storage
        replace_url = reverse(
            "resumes:replace",
            args=[resume.id],
        )

        replacement_file = SimpleUploadedFile(
            "updated-resume.pdf",
            b"%PDF-1.4 updated resume",
            content_type="application/pdf",
        )

        response = self.client.post(
            replace_url,
            {"file": replacement_file},
        )

        resume.refresh_from_db()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            resume.file.name,
            old_file_name,
        )
        self.assertTrue(
            storage.exists(old_file_name)
        )

    def test_feedback_requires_login(self):
        resume = self.create_resume()
        feedback_url = reverse(
            "resumes:feedback",
            args=[resume.id],
        )

        response = self.client.post(feedback_url)

        self.assertEqual(response.status_code, 401)

    @patch("resumes.api.get_resume_feedback")
    def test_user_receives_feedback_for_their_resume(
        self,
        feedback_function,
    ):
        resume = self.create_resume()
        feedback_url = reverse(
            "resumes:feedback",
            args=[resume.id],
        )
        feedback_function.return_value = (
            "- Add numbers to show your results"
        )
        self.sign_in()

        response = self.client.post(feedback_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["suggestions"],
            ["- Add numbers to show your results"],
        )
        feedback_function.assert_called_once_with(resume)


    @patch("resumes.api.get_resume_feedback")
    def test_user_cannot_request_feedback_for_another_resume(
        self,
        feedback_function,
    ):
        other_user = self.create_user("other-user")
        other_resume = self.create_resume(
            owner=other_user,
            filename="private-resume.pdf",
        )
        feedback_url = reverse(
            "resumes:feedback",
            args=[other_resume.id],
        )
        self.sign_in()

        response = self.client.post(feedback_url)

        self.assertEqual(response.status_code, 404)
        feedback_function.assert_not_called()


    @patch("resumes.api.get_resume_feedback")
    def test_ai_error_returns_503_json(
        self,
        feedback_function,
    ):
        resume = self.create_resume()
        feedback_url = reverse(
            "resumes:feedback",
            args=[resume.id],
        )
        feedback_function.side_effect = ResumeFeedbackError(
            "AI provider failed"
        )
        self.sign_in()

        response = self.client.post(feedback_url)

        self.assertEqual(response.status_code, 503)
        self.assertIn(
            "AI feedback is unavailable right now",
            response.json()["detail"],
        )


    @patch("resumes.api.get_resume_feedback")
    def test_feedback_rejects_get_requests(
        self,
        feedback_function,
    ):
        resume = self.create_resume()
        feedback_url = reverse(
            "resumes:feedback",
            args=[resume.id],
        )
        self.sign_in()

        response = self.client.get(feedback_url)

        self.assertEqual(response.status_code, 405)
        feedback_function.assert_not_called()


    def test_list_includes_own_resume_fields(self):
        resume = self.create_resume()
        self.sign_in()

        item = self.client.get(self.url).json()["results"][0]

        self.assertEqual(item["id"], resume.id)
        self.assertIn("url", item)
        self.assertIn("uploaded_at", item)

    def test_resume_file_is_prepared_for_openai(self):
        resume = self.create_resume()

        file_data = create_file_data(resume)

        self.assertTrue(
            file_data.startswith(
                "data:application/pdf;base64,"
            )
        )

    @patch("resumes.services.OpenAI")
    def test_service_returns_openai_feedback(
        self,
        openai_class,
    ):
        resume = self.create_resume()
        fake_response = MagicMock()
        fake_response.output_text = (
            "- Make your experience more specific"
        )
        openai_class.return_value.responses.create.return_value = (
            fake_response
        )

        feedback = get_resume_feedback(resume)

        self.assertEqual(
            feedback,
            "- Make your experience more specific",
        )
        openai_class.return_value.responses.create.assert_called_once()

    @patch("resumes.services.OpenAI")
    def test_service_rejects_empty_feedback(
        self,
        openai_class,
    ):
        resume = self.create_resume()
        fake_response = MagicMock()
        fake_response.output_text = "   "
        openai_class.return_value.responses.create.return_value = (
            fake_response
        )

        with self.assertRaises(ResumeFeedbackError):
            get_resume_feedback(resume)

    @patch("resumes.services.OpenAI")
    def test_service_handles_openai_errors(
        self,
        openai_class,
    ):
        resume = self.create_resume()
        openai_class.return_value.responses.create.side_effect = (
            RuntimeError("Provider failed")
        )

        with self.assertRaises(ResumeFeedbackError):
            get_resume_feedback(resume)