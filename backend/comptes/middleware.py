class NoCacheMiddleware:
    """Interdit toute mise en cache des réponses de l'API et des documents (retour arrière / session)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        r = self.get_response(request)
        if request.path.startswith('/api/'):
            r['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
            r['Pragma'] = 'no-cache'
            r['Expires'] = '0'
        return r
