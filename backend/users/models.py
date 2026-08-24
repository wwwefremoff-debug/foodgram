from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.constants import (
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    STR_REPR_MAX_LENGTH,
)


class User(AbstractUser):
    """Кастомный пользователь Foodgram."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )
    first_name = models.CharField('Имя', max_length=MAX_NAME_LENGTH)
    last_name = models.CharField('Фамилия', max_length=MAX_NAME_LENGTH)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:STR_REPR_MAX_LENGTH]


class Subscription(models.Model):
    """Подписка пользователя на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_subscriptions',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        )

    def __str__(self):
        return f'{self.user} → {self.author}'[:STR_REPR_MAX_LENGTH]
