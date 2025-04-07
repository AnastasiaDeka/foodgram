"""Настройки пагинации для API."""

from rest_framework.pagination import PageNumberPagination

from .constants import DEFAULT_PAGE_SIZE


class PaginatorWithLimit(PageNumberPagination):
    """Кастомный пагинатор с настройками по умолчанию.

    Позволяет указывать лимит через параметр запроса.
    """

    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "limit"
