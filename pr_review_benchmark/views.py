import json
import os

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def health(_request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse()


@require_GET
def meta(_request):
    data = {
        "git_revision": os.getenv("GIT_REVISION", "Unknown"),
    }
    return HttpResponse(json.dumps(data), content_type="application/json")


@require_GET
def simulate_403(_request):
    raise PermissionDenied


@require_GET
def simulate_500(_request):
    return HttpResponse(1 / 0)
