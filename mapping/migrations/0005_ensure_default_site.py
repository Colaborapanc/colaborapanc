import os

from django.db import migrations


LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "0.0.0.0"}


def _resolve_site_domain():
    explicit_domain = (
        os.environ.get("DJANGO_SITE_DOMAIN")
        or os.environ.get("DJANGO_DOMAIN")
        or os.environ.get("SITE_DOMAIN")
        or ""
    ).strip()
    if explicit_domain:
        return explicit_domain

    raw_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
    for raw_host in raw_hosts.split(","):
        host = raw_host.strip().split(":")[0].split("/")[0]
        if host and host not in LOCAL_HOSTS and not host.startswith("."):
            return host

    return "localhost"


def ensure_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")

    site_id = int(os.environ.get("DJANGO_SITE_ID", "1"))
    domain = _resolve_site_domain()
    site_name = (os.environ.get("DJANGO_SITE_NAME") or domain).strip() or domain

    Site.objects.update_or_create(
        id=site_id,
        defaults={"domain": domain, "name": site_name},
    )


def noop(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("mapping", "0004_scientific_core"),
    ]

    operations = [
        migrations.RunPython(ensure_site, noop),
    ]
