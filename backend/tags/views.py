from rest_framework import viewsets
from .models import Tag
from api.serializers import TagSerializer

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None
    