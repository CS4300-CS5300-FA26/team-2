from behave import given, then, when
from django.contrib.auth import get_user_model
from django.urls import reverse

from resumes.models import Resume


@given("I have two uploaded resumes and the first is my default")
def step_two_resumes(context):
    context.user = get_user_model().objects.create_user(
        username="default-resume-user",
        password="test-password-123",
        first_name="Test",
        last_name="User",
        email="default-resume-user@example.com",
    )
    context.test.client.force_login(context.user)

    context.first_resume = Resume.objects.create(
        owner=context.user,
        file="resumes/first-resume.pdf",
        is_default=True,
    )
    context.second_resume = Resume.objects.create(
        owner=context.user,
        file="resumes/second-resume.pdf",
    )


@when("I choose my second resume as the default")
def step_choose_second_resume(context):
    set_default_url = reverse(
        "resumes:set_default",
        args=[context.second_resume.id],
    )
    context.response = context.test.client.post(set_default_url)


@then("only my second resume is marked as the default")
def step_confirm_default(context):
    context.first_resume.refresh_from_db()
    context.second_resume.refresh_from_db()

    context.test.assertEqual(context.response.status_code, 200)
    context.test.assertFalse(context.first_resume.is_default)
    context.test.assertTrue(context.second_resume.is_default)
