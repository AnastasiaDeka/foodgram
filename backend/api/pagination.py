from rest_framework.pagination import PageNumberPagination

class PaginatorWithLimit(PageNumberPagination):
    """Кастомный пагинатор с настройками по умолчанию."""
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 50
