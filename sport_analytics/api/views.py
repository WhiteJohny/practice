from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    Player,
    Game,
    Team,
    Coach,
    PlayerPosition
)
from .serializers import (
    PlayerSerializer,
    GameSerializer,
    PlayerPositionSerializer,
    TeamSerializer,
    CoachSerializer
)


class BaseViewSet(viewsets.ModelViewSet):
    resource_name = None

    def get_response_data(self, data):
        return {"status": "success", self.resource_name: data}

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(self.get_response_data(response.data), status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(self.get_response_data(response.data), status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            self.get_response_data(serializer.data),
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(self.get_response_data(serializer.data), status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, partial=True, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"status": "success", "message": f"{self.resource_name[:-1].title()} успешно удален"},
            status=status.HTTP_200_OK
        )


class PlayerViewSet(BaseViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    resource_name = "players"

    # GET /players/{id}/stats/
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        player = self.get_object()
        return Response({
            "status": "success",
            "player_stats": {
                "games_played": player.games.count()
            }
        })


class GameViewSet(BaseViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    resource_name = "games"

    # GET/games/recent/
    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_games_count = 10
        recent_games = Game.objects.order_by('-datetime')[:recent_games_count]
        serializer = self.get_serializer(recent_games, many=True)
        return Response({
            "status": "success",
            "recent_games": serializer.data
        })


class PlayerPositionViewSet(BaseViewSet):
    pass


class TeamViewSet(BaseViewSet):
    pass


class CoachViewSet(BaseViewSet):
    pass
