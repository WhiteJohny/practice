import json

from rest_framework import serializers
from django.utils import timezone

from .models import (
    Team,
    Coach,
    Player,
    Game,
    PlayerPosition
)


class PlayerSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Player
        fields = [
            'id',
            'full_name',
            'birth_date',
            'experience',
            'team',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            'full_name': {
                'help_text': 'ФИО игрока.',
                'required': True
            },
            'birth_date': {
                'help_text': 'Дата рождения в формате YYYY-MM-DD.',
                'required': True
            },
            'experience': {
                'help_text': 'Стаж игрока.',
                'required': True
            }
        }

    def validate_birth_date(self, value):
        """Валидация даты рождения"""
        min_age = 16
        today = timezone.now().date()

        # Проверка, что дата не в будущем
        if value > today:
            raise serializers.ValidationError("Дата рождения не может быть в будущем.")

        # Проверка минимального возраста
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < min_age:
            raise serializers.ValidationError("Игрок должен быть старше 5 лет.")

        return value

    def validate_experience(self, value):
        """Валидация стажа"""
        if value < 0:
            raise serializers.ValidationError("Стаж не может быть отрицательным.")
        if value > 100:
            raise serializers.ValidationError("Стаж не может превышать 100 лет.")
        return value

    def validate(self, data):
        """Комплексная проверка данных"""
        birth_date = data.get('birth_date', self.instance.birth_date if self.instance else None)
        experience = data.get('experience', self.instance.experience if self.instance else 0)

        # Проверка соответствия стажа и возраста
        if birth_date and experience:
            today = timezone.now().date()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

            min_age = 16
            max_experience = max(0, age - min_age)

            if experience > max_experience:
                raise serializers.ValidationError({
                    "experience": f"Стаж не может превышать {max_experience} лет для данного возраста."
                })

        return data


class GameSerializer(serializers.ModelSerializer):
    teams = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        many=True,
        required=False
    )
    players = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        many=True,
        required=False
    )
    coaches = serializers.PrimaryKeyRelatedField(
        queryset=Coach.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Game
        fields = [
            'id',
            'datetime',
            'teams',
            'players',
            'coaches',
            'video_url',
            'result',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            'datetime': {
                'help_text': 'Дата и время проведения игры в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS).',
                'required': True
            },
            'video_url': {
                'help_text': 'Ссылка на видео игры.',
                'required': False
            },
            'result': {
                'help_text': 'Результат игры в формате "X:Y".',
                'required': False
            }
        }

    def validate_datetime(self, value):
        """Валидация даты и времени игры"""
        now = timezone.now()

        # Проверка, что дата не в будущем
        if value > now:
            raise serializers.ValidationError("Дата игры не может быть в будущем.")

        return value

    def validate_result(self, value):
        """Валидация формата результата"""
        if value and ':' not in value:
            raise serializers.ValidationError(
                'Результат должен содержать счёт в формате "X:Y".'
            )
        return value

    def validate(self, data):
        """Комплексная проверка данных игры"""
        teams = data.get('teams')
        players = data.get('players')
        coaches = data.get('coaches')

        if self.instance:
            if teams is None:
                teams = list(self.instance.teams.all())
            if players is None:
                players = list(self.instance.players.all())
            if coaches is None:
                coaches = list(self.instance.coaches.all())

        # Проверка, что все игроки принадлежат командам-участницам
        if teams is not None and players is not None:
            team_ids = {team.id for team in teams}
            invalid_players = []

            for player in players:
                # Игрок может быть без команды
                if player.team_id and player.team_id not in team_ids:
                    invalid_players.append(player.id)

            if invalid_players:
                raise serializers.ValidationError({
                    'players': f'Игроки {invalid_players} не принадлежат командам-участницам.'
                })

        # Проверка, что тренеры связаны с командами-участницами
        if teams is not None and coaches is not None:
            team_ids = {team.id for team in teams}
            invalid_coaches = []

            for coach in coaches:
                # Проверяем что тренер связан хотя бы с одной командой-участницей
                if not coach.teams.filter(id__in=team_ids).exists():
                    invalid_coaches.append(coach.id)

            if invalid_coaches:
                raise serializers.ValidationError({
                    'coaches': f'Тренеры {invalid_coaches} не связаны с командами-участницами.'
                })

        return data

    def create(self, validated_data):
        """Создание игры с обработкой отношений ManyToMany"""
        teams_data = validated_data.pop('teams', [])
        players_data = validated_data.pop('players', [])
        coaches_data = validated_data.pop('coaches', [])

        game = Game.objects.create(**validated_data)

        game.teams.set(teams_data)
        game.players.set(players_data)
        game.coaches.set(coaches_data)

        return game

    def update(self, instance, validated_data):
        """Обновление игры с обработкой отношений ManyToMany"""
        teams_data = validated_data.pop('teams', None)
        players_data = validated_data.pop('players', None)
        coaches_data = validated_data.pop('coaches', None)

        # Обновляем поля игры
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем связи если они были переданы
        if teams_data is not None:
            instance.teams.set(teams_data)
        if players_data is not None:
            instance.players.set(players_data)
        if coaches_data is not None:
            instance.coaches.set(coaches_data)

        return instance


class PlayerPositionSerializer(serializers.ModelSerializer):
    games = serializers.PrimaryKeyRelatedField(
        queryset=Game.objects.all(),
        help_text="ID игры",
        required=True
    )
    players = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        help_text="ID игрока",
        required=True
    )

    class Meta:
        model = PlayerPosition
        fields = [
            'id',
            'games',
            'players',
            'timestamp',
            'x_coordinate',
            'y_coordinate',
            'z_coordinate',
            'speed',
            'additional_parameters',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'timestamp': {
                'help_text': 'Временная метка в секундах от начала игры',
                'required': True
            },
            'x_coordinate': {
                'help_text': 'Координата X',
                'required': False
            },
            'y_coordinate': {
                'help_text': 'Координата Y',
                'required': False
            },
            'z_coordinate': {
                'help_text': 'Координата Z',
                'required': False
            },
            'speed': {
                'help_text': 'Скорость игрока',
                'required': False
            },
            'additional_parameters': {
                'help_text': 'Дополнительные параметры в формате JSON',
                'required': False
            }
        }

    def validate_timestamp(self, value):
        """Базовая валидация временной метки"""
        if value < 0:
            raise serializers.ValidationError(
                "Временная метка не может быть отрицательной."
            )
        return value

    def validate(self, data):
        """Комплексная валидация"""
        # Проверка, что игрок участвует в указанной игре
        games = data.get('games')
        players = data.get('players')

        if games and players:
            if not games.players.filter(id=players.id).exists():
                raise serializers.ValidationError({
                    "players": "Игрок не участвует в указанной игре."
                })

        return data

    def to_internal_value(self, data):
        """Оптимизация обработки данных"""
        if 'additional_parameters' in data and isinstance(data['additional_parameters'], dict):
            data = data.copy()
            data['additional_parameters'] = json.dumps(data['additional_parameters'])
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Оптимизация представления данных"""
        representation = super().to_representation(instance)

        if 'additional_parameters' in representation and representation['additional_parameters']:
            representation['additional_parameters'] = json.loads(representation['additional_parameters'])

        return representation


class TeamSerializer(serializers.ModelSerializer):
    coaches = serializers.PrimaryKeyRelatedField(
        queryset=Coach.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'city_region',
            'coaches',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            'name': {
                'help_text': 'Название команды.',
                'required': True
            },
            'city_region': {
                'help_text': 'Город/Регион команды.',
                'required': True
            }
        }

    def create(self, validated_data):
        """Создание команды с обработкой отношений ManyToMany"""
        coaches_data = validated_data.pop('coaches', [])

        team = Team.objects.create(**validated_data)

        team.coaches.set(coaches_data)

        return team

    def update(self, instance, validated_data):
        """Обновление команды с обработкой отношений ManyToMany"""
        coaches_data = validated_data.pop('coaches', None)

        # Обновляем поля команды
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем связи если они были переданы
        if coaches_data is not None:
            instance.coaches.set(coaches_data)

        return instance


class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = [
            'id',
            'full_name',
            'contact_data',
            'birth_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            'full_name': {
                'help_text': 'ФИО тренера.',
                'required': True
            },
            'contact_data': {
                'help_text': 'Контактные данные тренера.',
                'required': True
            },
            'birth_date': {
                'help_text': 'Дата рождения тренера в формате YYYY-MM-DD.',
                'required': True
            }
        }
