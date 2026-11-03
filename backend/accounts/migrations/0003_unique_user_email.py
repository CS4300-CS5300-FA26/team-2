from django.db import migrations


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
        migrations.RunSQL(
            "CREATE UNIQUE INDEX accounts_user_email_ci_uniq "
            "ON auth_user (LOWER(email)) WHERE email <> '';",
            reverse_sql="DROP INDEX accounts_user_email_ci_uniq;",
        ),
    ]
