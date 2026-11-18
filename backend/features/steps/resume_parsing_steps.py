from unittest.mock import patch

from behave import then, when
from django.urls import reverse


@when("the system parses my resume into profile fields")
def step_parse_resume(context):
    parse_url = reverse(
        "resumes:parse",
        args=[context.resume.id],
    )

    with patch(
        "resumes.api.parse_resume_fields"
    ) as parse_function:
        parse_function.return_value = {
            "skills": "Python",
            "experience": "Built a web application",
            "education": "Software engineering student",
        }
        context.response = context.test.client.post(parse_url)


@when("I correct one of the parsed fields")
def step_edit_parsed_fields(context):
    fields_url = reverse(
        "resumes:update_fields",
        args=[context.resume.id],
    )

    context.response = context.test.client.post(
        fields_url,
        {
            "skills": "Python, Django",
            "experience": "Built a web application",
            "education": "Software engineering student",
        },
    )


@then("my corrected resume fields are saved")
def step_confirm_parsed_fields(context):
    context.resume.refresh_from_db()

    context.test.assertEqual(context.response.status_code, 200)
    context.test.assertEqual(
        context.resume.skills,
        "Python, Django",
    )
    context.test.assertEqual(
        context.resume.experience,
        "Built a web application",
    )
    context.test.assertEqual(
        context.resume.education,
        "Software engineering student",
    )
