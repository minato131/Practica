from django import template

register = template.Library()

@register.filter
def filter_by_status(queryset, status_name):
    """Фильтрация queryset по статусу автомобиля"""
    return [obj for obj in queryset if obj.status.name == status_name]

@register.filter
def filter_by(queryset, filter_name):
    """Фильтрация queryset по имени фильтра"""
    if filter_name == "is_superuser":
        return [obj for obj in queryset if obj.is_superuser]
    elif filter_name == "is_staff":
        return [obj for obj in queryset if obj.is_staff and not obj.is_superuser]
    elif filter_name == "is_staff_false":
        return [obj for obj in queryset if not obj.is_staff and not obj.is_superuser]
    return queryset

@register.filter
def add(value, arg):
    """Добавление значения"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except Exception:
            return ''

@register.filter
def get_item(dictionary, key):
    """Получение элемента из словаря"""
    return dictionary.get(key)
@register.filter
def filter_by_booking_status(queryset, status_name):
    """Фильтрация queryset по статусу бронирования"""
    return [obj for obj in queryset if obj.status.name == status_name]