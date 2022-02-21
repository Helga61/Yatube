from django.core.paginator import Paginator

from .conf import NUMBER_OF_POSTED


def get_page(queryset, request):
    paginator = Paginator(queryset, NUMBER_OF_POSTED)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
