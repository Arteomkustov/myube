# context_processors
from .models import Subscription


def get_subscribes_context(request):
    m = Subscription.objects.all()
    return {'s':  m}
