from django.core.exceptions import ValidationError


def validate_username(value):
    if value == 'me':
        raise ValidationError('Имя пользователя не может быть - me')


def min_value_validator(value):
    if value < 1:
        raise ValidationError(f'{value} меньше 1 минуты')
