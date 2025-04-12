# Проект Foodgram

Проект Foodgram представляет собой систему для публикации рецептов, где пользователи могут подписываться на других авторов, создавать рецепты и управлять ими. Включает API для взаимодействия с рецептами, подписками и пользователями. Также предусмотрен фронтенд для отображения рецептов и управления аккаунтами.

---

### Проект доступен по доменному имени:

[https://aderline.ru](https://aderline.ru)


---


# Инструкция по развертыванию в Docker

## Подготовка и запуск проекта

### 1. Клонировать репозиторий

Для начала клонируйте репозиторий:

```bash
git clone https://github.com/AnastasiaDeka/foodgram.git
cd foodgram
```
### 2.Установите Docker и Docker Compose:

- **Для Mac:**

Скачайте и установите Docker Desktop для Mac с официального сайта Docker.

Docker Compose уже будет установлен вместе с Docker Desktop.

- **Для Windows:**

Скачайте и установите Docker Desktop для Windows с официального сайта Docker.

Docker Compose также будет установлен вместе с Docker Desktop.

### 3. Построение Docker контейнера

Для сборки контейнера используйте команду:

```
docker-compose up --build
```

### 3. Запуск контейнера
После того как сборка завершится, контейнер автоматически запустится.

### 4. Остановка контейнера
Чтобы остановить контейнер, выполните команду:

```
docker-compose down
```

### 5. Порты
Веб-приложение будет доступно по адресу http://localhost.

Спецификация API доступна по адресу http://localhost/api/docs/.

---

# Как наполнить БД данными

Для наполнения базы данных данными выполните следующие шаги:

1. **Миграции базы данных:**
    Сначала выполните миграции, чтобы создать необходимые таблицы в базе данных:
    ```
    docker-compose exec foodgram_backend python manage.py migrate
    ```

2. **Заполнение через Django admin (если используется Django):**
    Если используется Django, войдите в административную панель по адресу [http://localhost/admin](http://localhost/admin), добавьте необходимые данные через интерфейс.

---


# Стек технологий

В проекте используются следующие технологии:

В проекте используются следующие технологии:

- **Backend**: Django + Django REST Framework

- **База данных: PostgreSQL**

- **Docker**: для контейнеризации приложения

- **Swagger/OpenAPI**: для документирования API

- **Nginx**: для проксирования и обслуживания статических файлов

- **Gunicorn**: WSGI сервер для работы с Django

- **CI/CD**: GitHub Actions для автоматизации сборки, тестирования и деплоя

---

# Настройка удаленного сервера
## Для работы с удаленным сервером (на Mac или Windows):

## Вход на сервер
Подключитесь к удаленному серверу с помощью SSH:
```
ssh <username>@<host>
```

### Установите Docker:
Для Mac и Windows установите Docker Desktop (ссылка дана выше).

### Установите Docker Compose:
Для Mac и Windows Docker Compose будет установлен автоматически вместе с Docker Desktop.

### Подготовьте конфигурационные файлы:
Отредактируйте файл infra/nginx.conf локально, в строке server_name впишите свой IP.

### Скопируйте файлы docker-compose.yml и nginx.conf на сервер:

```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```
### Создайте файл .env:
Создайте .env файл и добавьте следующие переменные:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<имя базы данных postgres>
DB_USER=<пользователь бд>
DB_PASSWORD=<пароль>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<секретный ключ проекта django>
```

Для работы с GitHub Actions добавьте в Secrets GitHub переменные окружения для работы (описано ниже).

## Деплой на сервер
### Соберите Docker контейнер:

```
sudo docker-compose up -d --build
```
После успешной сборки на сервере выполните следующие команды (только после первого деплоя):

Соберите статические файлы:
```
sudo docker-compose exec backend python manage.py collectstatic --noinput
```
Примените миграции:

```
sudo docker-compose exec backend python manage.py migrate --noinput
```
Загрузите ингредиенты в базу данных (необязательно):

```
sudo docker-compose exec backend python manage.py loaddata fixtures/ingredients.json
```
Создайте суперпользователя Django:

``` 
sudo docker-compose exec backend python manage.py createsuperuser

```
Теперь проект будет доступен по вашему IP, и вы сможете управлять им через административную панель или API.


---
# Переменные окружения для GitHub Actions

Для корректной работы с GitHub Actions необходимо добавить следующие переменные окружения в разделе **Secrets > Actions** вашего репозитория:

### Переменные для проекта:

- **SECRET_KEY**: Секретный ключ Django проекта.
- **DOCKER_PASSWORD**: Пароль от Docker Hub.
- **DOCKER_USERNAME**: Логин Docker Hub.
- **HOST**: Публичный IP сервера.
- **USER**: Имя пользователя на сервере.
- **PASSPHRASE**: (если SSH-ключ защищен паролем).
- **SSH_KEY**: Приватный SSH-ключ.
- **TELEGRAM_TO**: ID телеграм-аккаунта для отправки сообщений.
- **TELEGRAM_TOKEN**: Токен бота, отправляющего сообщения.

### Переменные для базы данных:

- **DB_ENGINE**: Тип базы данных для Django (`django.db.backends.postgresql`).
- **POSTGRES_DB**: Имя базы данных для PostgreSQL.
- **POSTGRES_USER**: Пользователь для подключения к базе данных PostgreSQL.
- **POSTGRES_PASSWORD**: Пароль для пользователя базы данных PostgreSQL.
- **DB_HOST**: Хост базы данных (например, `db`).
- **DB_PORT**: Порт базы данных (по умолчанию `5432`).
---

# Пример запросов и ответов

Пример запросов к API:

### GET /api/users/?limit=1&page=1

Этот запрос возвращает список пользователей с пагинацией (по одному пользователю на страницу).

>Статус 200 - удачное выполнение запроса

``` json
{
    "count": 4,
    "next": "http://127.0.0.1:8000/api/users/?limit=1&page=2",
    "previous": null,
    "results": [
        {
            "id": 5,
            "username": "vasya.ivanov",
            "email": "vivanov@yandex.ru",
            "first_name": "Вася",
            "last_name": "Иванов",
            "avatar": null,
            "is_subscribed": false
        }
    ]
}
```

### POST /api/recipes/

Это пример ответа от API, который предоставляет информацию о рецепте, созданном вторым пользователем.

>Статус 200 - удачное выполнение запроса

``` json
{{
    "id": 100,
    "tags": [
        {
            "id": 1,
            "name": "Завтрак",
            "slug": "breakfast"
        },
        {
            "id": 2,
            "name": "Обед",
            "slug": "lunch"
        }
    ],
    "name": "Нечто съедобное (это не точно)",
    "text": "Приготовьте как нибудь эти ингредиеты",
    "cooking_time": 5,
    "author": {
        "id": 6,
        "username": "second-user",
        "email": "second_user@email.org",
        "first_name": "Андрей",
        "last_name": "Макаревский",
        "avatar": null,
        "is_subscribed": false
    },
    "is_favorited": false,
    "is_in_shopping_cart": false,
    "image": "http://127.0.0.1:8000/media/recipes_images/6d123ef9-04ff-4726-82d6-4058b1adbca3.png",
    "ingredients": [
        {
            "id": 170,
            "name": "Буррата",
            "measurement_unit": "г",
            "amount": 10
        },
        {
            "id": 1195,
            "name": "Панифарин",
            "measurement_unit": "г",
            "amount": 20
        }
    ]
}
```
---

## Автор


- [Декапольцева Анастасия](https://github.com/AnastasiaDeka)
