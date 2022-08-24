# praktikum_new_diplom
# foodgram-project-react
## Описание проекта.
Проект foodgram-project-react сервис, на котором пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

Данный проект реализован на библиотеке djangorestframework.

## Как запустить проект: 
Пересобрать контейнер и запустить контейнер:
```
docker-compose up -d --build
```
Выполнить миграции:
```
docker-compose exec web python manage.py migrate
```
Создать суперпользователя:
```
docker-compose exec web python manage.py createsuperuser
```
Cобрать статику:
```
docker-compose exec web python manage.py collectstatic --no-input
```
Проект доступен по адресу:
```
http://localhost/
```

### Примеры обращений к API:

#### Самостоятельно зарегистрироваться и получить код подтвердения для получения токена:

Обратиться по методу Post на - ``` http://{url}/api/api/users/ ```
В теле запроса передать параметры email, username, first_name, last_name, password и их значения. После этого, если пользователь новыйй произойдет его регистрация, если пользователь уже существует, то регистрация не произойдет:
Пример тела запроса:
```
{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Пупкин",
  "password": "Qwerty1234"
}
```
#### Получить токен для авторизации пользователя:

Обратиться по методу Post на - ``` http://{url}/api/auth/token/login/ ```
В теле запроса передать параметры email и password и их значения.
Полученный токен использовать для авторизации в сервисе api по методу bearer.
Пример тела запроса:
```
{
  "password": "123456",
  "email": "K@mail.ru"
}
```
Пример ответа:
```
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjUzOTI3ODgxL"
}
```
#### Получить список рецептов:

Метод Get - ``` http://{url}/api/recipes/ ```

Ответ
```
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "color": "#E26C2D",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Пупкин",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}

```
#### Добавить рецепт (доступно только авторизованному пользователю):

Обратиться по методу Post на эндпойнт - ``` http://{url}/api/recipes/ ```
В теле запроса передать название рецепта, игредиенты, теги, картинка, время приготовления
Тело запроса:
```
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

#### Просмотреть определенный рецепт:

Обратиться по методу Get на эндпойнт - ``` http://{url}/api/recipes/{recipes_id}/ ```
Ответ:
```
{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "color": "#E26C2D",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "string",
    "first_name": "Вася",
    "last_name": "Пупкин",
    "is_subscribed": false
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
  "text": "string",
  "cooking_time": 1
}

```
Авторизованному пользователю на данном эндпойнте также доступны методы Patch и Delete.

#### Скачать файл со списком покупок:

Метод Get - ``` http://{url}/api/recipes/download_shopping_cart/ ```

#### Добавить рецепт в список покупок:
Доступно только авторизованным пользователям.

Метод Get - ``` http://{url}/api/recipes/{recipe_id}/shopping_cart/ ```

Ответ:
```
{
  "id": 0,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
  "cooking_time": 1
}
```

Метод Delete
Удалить рецепт из списка покупок - ``` http://{url}/api/recipes/{recipe_id}/shopping_cart/ ```

#### Добавить рецепт в избранное:
Доступно только авторизованному пользователю.
Отправить запрос по методу Post - ``` http://{url}/api/recipes/{id}/favorite/ ```

Тело запроса:
```
{
  "id": 0,
  "name": "string",
  "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
  "cooking_time": 1
}
```
#### Удалить рецепт из избранного:
Отправить запрос по методу Delete - ``` http://{url}/api/recipes/{id}/favorite/ ```

#### Мои подписки:
Возвращает пользователей, на которых подписан текущий пользователь. В выдачу добавляются рецепты.
Отправить запрос по методу Get - ``` http://{url}/api/users/subscriptions/ ```

#### Подписаться на пользователя
Доступно только авторизованным пользователям.
Отправить запрос по методу Post - ``` http://{url}/api/users/{id}/subscriptions/ ```

Тело запроса:
```
{
  "email": "user@example.com",
  "id": 0,
  "username": "string",
  "first_name": "Вася",
  "last_name": "Пупкин",
  "is_subscribed": true,
  "recipes": [
    {
      "id": 0,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
      "cooking_time": 1
    }
  ],
  "recipes_count": 0
}
```
### Отписаться от пользователя
Доступно только авторизованным пользователям.
Отправить запрос по методу Delete - ``` http://{url}/api/users/{id}/subscriptions/ ```

### Список ингредиентов
Список ингредиентов с возможностью поиска по имени.
Отправить запрос по методу Get - ``` http://{url}/api/ingredients/{id}/ ```

