[![Practicum_bot deploy](https://github.com/hlystovea/practicum_bot/actions/workflows/main.yml/badge.svg)](https://github.com/hlystovea/practicum_bot/actions/workflows/main.yml)

# Practicum_bot (Телеграм бот)

### Описание
Разработан для студентов Яндекс.Практикум. Бот запрашивает статус домашки через API Яндекс.Практикум и присылает уведомления в телеграм. В качестве резерва используется отправка на email. 

### Технологии
- Python 3.9

### Начало работы

1. Склонируйте проект:

```git clone https://github.com/hlystovea/practicum_bot.git```  


2. Получите токен для доступа к API Яндекс.Практикум [(инструкция)](https://code.s3.yandex.net/backend-developer/learning-materials/delugov/Практикум.Домашка%20Шпаргалка.pdf).

4. Создайте файл .env по примеру env.example.


3. Запустите Docker контейнеры:

```docker-compose up -d```

4. Бот начнет отслеживание статуса домашки. 
