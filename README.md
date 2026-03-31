Event Booking Platform

Микросервисная система бронирования билетов (React + Python + MSSQL + Redis + RabbitMQ).

===========НАСТРОЙКА============

1. Запуск контейнеров - docker-compose up --build

2. Настройка БД: 

    MSSQL Login: 
    localhost:1433, логин: sa, пароль: Qies$12!

    Script: 
    CREATE DATABASE BookingDB; GO
    USE BookingDB; GO

    CREATE TABLE Users (Id INT IDENTITY(1,1) PRIMARY KEY, Username NVARCHAR(50) UNIQUE NOT NULL, PasswordHash NVARCHAR(256) NOT NULL, Role NVARCHAR(20) DEFAULT 'user');
    CREATE TABLE Events (Id INT IDENTITY(1,1) PRIMARY KEY, Title NVARCHAR(100) NOT NULL, Description NVARCHAR(255), TotalSeats INT NOT NULL, AvailableSeats INT NOT NULL);
    CREATE TABLE Bookings (Id INT IDENTITY(1,1) PRIMARY KEY, UserId INT FOREIGN KEY REFERENCES Users(Id), EventId INT FOREIGN KEY REFERENCES Events(Id), Status NVARCHAR(20) DEFAULT 'CONFIRMED');

3. Создание админа (с паролем 123) через БД: 

    INSERT INTO Users (Username, PasswordHash, Role) 
    VALUES (
        'admin', 
        'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 
        'admin'
    );

===============ИСПОЛЬЗОВАНИЕ===========

1. Открыть http://localhost:3000
2. Зайти под админом и создать событие
3. Зарегестрировать обычного пользователя и забронировать событие
4. Вернуться на сторону админа и просмотреть логи, забронированные места и пользователей

RabbitMQ - (Очереди/Логи): http://localhost:15672 (guest / guest)
