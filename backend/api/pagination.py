from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация с параметром limit из OpenAPI."""

    page_size_query_param = 'limit'
