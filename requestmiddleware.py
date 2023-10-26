import threading
lock = threading.Lock()


class RequestMiddleware:
    request_count = 0
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(request.get_full_path())
        response = self.get_response(request)
        path = request.get_full_path()
        if path not in ('/request-count/','/request-count/reset/'):
            with lock:
                RequestMiddleware.request_count += 1
        return response