from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'recipes_count',
        'subscribers_count',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('username',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Аватар', {'fields': ('avatar',)}),
    )

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, obj):
        return obj.subscriptions_to_author.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user', 'author')
