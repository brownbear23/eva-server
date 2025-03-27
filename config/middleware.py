from django.shortcuts import redirect
from django.conf import settings


EXEMPT_URLS = [
    settings.LOGIN_URL.lstrip('/'),
    '/accounts/logout/',
    '/accounts/login/',
    '/static/',  # Optional: let CSS/JS load
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        path = request.path
        # print("Authenticated?", request.user.is_authenticated, "Path:", path)

        if user and not user.is_authenticated:
            if not any(path.startswith(url) for url in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)


        return self.get_response(request)

