"""Формирование файла списка покупок."""


def format_shopping_list(ingredients):
    """Собрать текстовый список покупок из агрегированных ингредиентов."""
    lines = ['Список покупок:\n']
    for ingredient in ingredients:
        lines.append(
            f"- {ingredient['name']} ({ingredient['unit']}) — "
            f"{ingredient['total']}"
        )
    return '\n'.join(lines)
