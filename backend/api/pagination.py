from rest_framework.pagination import PageNumberPagination

class PaginatorWithLimit(PageNumberPagination):
    """Кастомный пагинатор с настройками по умолчанию."""
    page_size = 6
    page_size_query_param = 'limit'  # Позволяет клиенту менять размер страницы через параметр 'limit'
    max_page_size = 50  # Максимальное количество объектов на странице

    def get_page_size(self, request):
        page_size = super().get_page_size(request)
        print(f"Page size requested: {page_size}")  # Отладочное сообщение
        print(f"Request parameters: {request.GET}")  # Печать всех параметров запроса
        if page_size > self.max_page_size:
            print(f"Page size exceeds max_page_size. Setting to {self.max_page_size}")
            page_size = self.max_page_size
        return page_size
