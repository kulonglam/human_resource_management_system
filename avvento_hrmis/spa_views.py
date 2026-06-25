from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View


class ReactAppView(View):
    """Serve the React SPA index.html for client-side routing."""

    def get(self, request, *args, **kwargs):
        index_path = Path(settings.REACT_BUILD_DIR) / 'index.html'
        if not index_path.exists():
            return HttpResponse(
                'React frontend is not built. Run: cd frontend && npm install && npm run build',
                status=503,
                content_type='text/plain',
            )
        return HttpResponse(index_path.read_text(encoding='utf-8'), content_type='text/html')
