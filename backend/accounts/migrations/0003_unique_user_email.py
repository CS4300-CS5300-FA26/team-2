from django.db import migrations
from django.db.models.functions import Lower


# Review fix for PR #77: creating the unique index below fails if the database
# already has two accounts whose emails differ only by capitals. Before adding it,
# keep the email on the oldest account and clear it on the newer ones. Those users
# are sent back to step 2 (enter an email) and step 3 (verify it) at their next login.
def clear_duplicate_emails(apps, schema_editor):
    User = apps.get_model("auth", "User")
    EmailVerification = apps.get_model("accounts", "EmailVerification")
    seen = set()
    for user in User.objects.exclude(email="").annotate(key=Lower("email")).order_by("id"):
        if user.key in seen:
            User.objects.filter(pk=user.pk).update(email="")
            EmailVerification.objects.update_or_create(user_id=user.pk, defaults={"code": "", "attempts": 0})
        else:
            seen.add(user.key)


# US1.2 review fix: two accounts can't share an email, even if two sign-ups
# save at the same moment. Django's User table doesn't enforce this, so we add
# a unique index on the lowercased email. Blank emails (old accounts) are skipped.
# Works on both PostgreSQL and SQLite.
class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_verification_expiry"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(clear_duplicate_emails, migrations.RunPython.noop),
        migrations.RunSQL(
            "CREATE UNIQUE INDEX accounts_user_email_ci_uniq "
            "ON auth_user (LOWER(email)) WHERE email <> '';",
            reverse_sql="DROP INDEX accounts_user_email_ci_uniq;",
        ),
    ]
