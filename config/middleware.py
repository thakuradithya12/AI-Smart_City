class BrowserPolicyHeadersMiddleware:
    """Set browser policies that are not covered by Django's security middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(self)")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        # Complaint and workspace HTML can contain personal data; browsers and shared caches must not retain it.
        if response.get("Content-Type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store"
        return response
