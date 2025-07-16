import json

from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.core.exceptions import ValidationError


class BaseModel(models.Model):
    created_at = models.DateTimeField(
        'Дата и время добавления в систему',
        auto_now_add=True  # На добавление
    )
    updated_at = models.DateTimeField(
        'Дата и время обновления в системе',
        auto_now=True  # На обновление
    )

    class Meta:
        abstract = True
    def __str__(self):
        return (f'Время создания - {self.created_at}.'
                f' Время обновления - {self.updated_at}')


class Team(BaseModel):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    name = models.CharField(
        'Название команды',
        max_length=255
    )
    city_region = models.CharField(
        'Город/Регион',
        max_length=255
    )

    coaches = models.ManyToManyField(
        'Coach',
        related_name='teams',
        verbose_name='Тренеры'
    )

    players = models.ManyToManyField(
        'Player',
        related_name='teams',
        verbose_name='Игроки'
    )

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'

    def __str__(self):
        return self.name


class Coach(BaseModel):
    FIO_MAX_LENGTH = 255
    CONTACT_MAX_LENGTH = 255

    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )

    full_name = models.CharField(
        'ФИО',
        max_length=FIO_MAX_LENGTH
    )
    contact_data = models.CharField(
        'Контактные данные',
        max_length=CONTACT_MAX_LENGTH
    )
    birth_date = models.DateField(
        'Дата рождения'
    )
    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'

    def __str__(self):
        return self.full_name


class Player(BaseModel):
    FIO_MAX_LENGTH = 255
    MIN_EXPERIENCE = 0
    MAX_EXPERIENCE = 100

    class Meta:
        # MIN_EXPERIENCE = 0
        # MAX_EXPERIENCE = 100

        # constraints = [
        #     # Проверка диапазона стажа
        #     models.CheckConstraint(
        #         check=models.Q(experience__gte=models.F('MIN_EXPERIENCE')) & models.Q(experience__lte=models.F('MAX_EXPERIENCE')),
        #         name='experience_range'
        #     )
        # ]
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'

    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    full_name = models.CharField(
        'ФИО',
        max_length=FIO_MAX_LENGTH
    )
    birth_date = models.DateField('Дата рождения')
    experience = models.IntegerField(
        'Стаж',
        # max_length=MAX_EXPERIENCE,
        default=MIN_EXPERIENCE
    )
    # team = models.ForeignKey(
    #     Team,
    #     on_delete=models.SET_NULL,
    #     related_name='players',
    #     null=True,
    #     blank=True,
    #     verbose_name='Команда'
    # )
    anthropometric = JSONField(
        'Антропометрические данные',
        null=True,
        blank=True
    )

    def clean(self):
        # Проверка даты рождения
        if self.birth_date > timezone.now().date():
            raise ValidationError({'birth_date': 'Дата рождения не может быть в будущем'})

        # Проверка антропометрических данных
        if self.anthropometric:
            try:
                anthropometric_data = json.loads(json.dumps(self.anthropometric))  # dict(self.anthropometric)

                required_fields = ['вес', 'рост']
                for field in required_fields:
                    if field not in anthropometric_data:
                        raise ValidationError(
                            {'anthropometric': f'Отсутствует обязательное поле: {field}'}
                        )

                    value = anthropometric_data[field]
                    if not isinstance(value, (int, float)) or value <= 0:
                        raise ValidationError(
                            {'anthropometric': f'Некорректное значение для поля {field}'}
                        )
            except TypeError:
                raise ValidationError(
                    {'anthropometric': 'Данные должны быть в формате словаря'}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class Game(BaseModel):
    URL_MAX_LENGTH = 500

    class Meta:
        constraints = [
            # Игра не может быть в будущем
            models.CheckConstraint(
                check=models.Q(datetime__lte=timezone.now()),
                name='game_date_past'
            )
        ]
        ordering = ['-datetime']
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    datetime = models.DateTimeField('Дата и время проведения')
    teams = models.ManyToManyField(
        'Team',
        related_name='games',
        verbose_name='Команды-участники'
    )
    players = models.ManyToManyField(
        'Player',
        related_name='games',
        verbose_name='Игроки'
    )
    coaches = models.ManyToManyField(
        'Coach',
        related_name='games',
        verbose_name='Тренеры'
    )
    video_url = models.URLField(
        'Ссылка на видео',
        max_length=URL_MAX_LENGTH,
        null=True,
        blank=True
    )
    result = models.TextField(
        'Результат',
        null=True,
        blank=True
    )

    def clean(self):
        # Проверка, что дата игры не в будущем
        if self.datetime > timezone.now():
            raise ValidationError(
                {'datetime': 'Дата игры не может быть в будущем'}
            )

        # Проверка формата результата
        if self.result and ':' not in self.result:
            raise ValidationError(
                {'result': 'Результат должен содержать счёт в формате "X:Y"'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Игра {self.id} - {self.datetime}"


class PlayerPosition(BaseModel):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    games = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='player_positions',
        verbose_name='Игра'
    )
    players = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='player_positions',
        verbose_name='Игрок'
    )
    timestamp = models.FloatField(
        'Временная метка (секунда)',
        help_text='В секундах от начала игры'
    )
    x_coordinate = models.FloatField(
        'Координата X',
        null=True,
        blank=True
    )
    y_coordinate = models.FloatField(
        'Координата Y',
        null=True,
        blank=True
    )
    z_coordinate = models.FloatField(
        'Координата Z',
        null=True,
        blank=True
    )
    speed = models.FloatField(
        'Скорость',
        null=True,
        blank=True
    )
    additional_parameters = JSONField(
        'Дополнительные параметры',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Позиция игрока'
        verbose_name_plural = 'Позиции игроков'

    def __str__(self):
        return f"Позиция игрока {self.player} в игре {self.game} на {self.timestamp} секунде"

