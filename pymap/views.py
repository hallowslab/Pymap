from django.http import HttpResponse, JsonResponse
from .tasks import ping

# Create your views here.

def index(request):
    return HttpResponse("Hello from Pymap App!")


def test_celery(request):
    result = ping.delay()  # executes asynchronously
    return JsonResponse({"task_id": result.id, "status": "queued"})