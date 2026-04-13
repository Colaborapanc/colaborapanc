# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import JsonResponse

# ---- Opção: título do Admin (cosmético) ----
admin.site.site_header = "ColaboraPANC • Administração"
admin.site.site_title = "ColaboraPANC Admin"
admin.site.index_title = "Painel de Controle"

# ---- Healthcheck simples (útil p/ monitoramento/uptime) ----
def healthcheck(_request):
    return JsonResponse({"status": "ok"}, status=200)

urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),

    # App principal
    path("", include("mapping.urls")),

    # Autenticação com django-allauth
    path("accounts/", include("allauth.urls")),

    # Healthcheck
    path("healthz/", healthcheck, name="healthcheck"),
]

# ---- Opcional: APIs (DRF). Só carrega se você criar um app api/urls.py ----
try:
    urlpatterns += [path("api/", include("api.urls"))]  # ex: api/urls.py com DRF routers
except Exception:
    # Sem problema se não existir
    pass

# ---- Opcional: Debug Toolbar (somente em DEBUG e se instalado) ----
if settings.DEBUG:
    try:
        import debug_toolbar  # type: ignore
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    except Exception:
        pass

    # Servir arquivos de mídia em DEV
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Servir arquivos estáticos via app django.contrib.staticfiles em DEV
urlpatterns += staticfiles_urlpatterns()

