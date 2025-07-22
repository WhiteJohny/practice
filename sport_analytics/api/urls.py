from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (
    PlayerViewSet,
    GameViewSet,
    PlayerPositionViewSet,
    TeamViewSet,
    CoachViewSet
)

router = DefaultRouter()

router.register(r'players', PlayerViewSet, basename='player')
router.register(r'games', GameViewSet, basename='game')
router.register(r'player_positions', PlayerPositionViewSet, basename='player_position')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'coaches', CoachViewSet, basename='coach')


urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('', include(router.urls))
]
