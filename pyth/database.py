import sqlite3
import os

conn = sqlite3.connect("excursion.db")


def main():
    conn = sqlite3.connect('excursion.db')
    cursor = conn.cursor()

    # =========================
    # Таблица гидов
    # =========================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE,
            experience_years INTEGER NOT NULL CHECK(experience_years >= 0)
        )
    ''')

    # =========================
    # Таблица экскурсий
    # =========================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS excursions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            city TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            guide_id INTEGER NOT NULL,
            FOREIGN KEY (guide_id)
            REFERENCES guides(id)
            ON DELETE RESTRICT
        )
    ''')

    # =========================
    # Таблица клиентов
    # =========================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')

    # =========================
    # Таблица бронирований
    # =========================

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            excursion_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            people_count INTEGER NOT NULL CHECK(people_count > 0),

            FOREIGN KEY (client_id)
            REFERENCES clients(id)
            ON DELETE RESTRICT,

            FOREIGN KEY (excursion_id)
            REFERENCES excursions(id)
            ON DELETE RESTRICT
        )
    ''')

    # =========================
    # Добавляем гидов
    # =========================

    guides = [
        ('Иван Петров', 5),
        ('Анна Смирнова', 8),
        ('Алексей Волков', 3),
        ('Мария Соколова', 10),
        ('Дмитрий Орлов', 6)
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO guides
        (full_name, experience_years)
        VALUES (?, ?)
    ''', guides)

    # =========================
    # Получаем id гидов
    # =========================

    cursor.execute('SELECT id, full_name FROM guides')

    guides_dict = {
        name: id for id, name in cursor.fetchall()
    }

    # =========================
    # Добавляем экскурсии
    # =========================

    excursions = [
        ('Обзорная экскурсия', 'Москва', 2500,
         guides_dict['Иван Петров']),

        ('Ночной Петербург', 'Санкт-Петербург', 4000,
         guides_dict['Анна Смирнова']),

        ('Исторический центр', 'Казань', 3000,
         guides_dict['Алексей Волков']),

        ('Горы Кавказа', 'Сочи', 5500,
         guides_dict['Мария Соколова']),

        ('Золотое кольцо', 'Владимир', 4500,
         guides_dict['Дмитрий Орлов'])
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO excursions
        (title, city, price, guide_id)
        VALUES (?, ?, ?, ?)
    ''', excursions)

    # =========================
    # Добавляем клиентов
    # =========================

    clients = [
        ('Александр Иванов',
         '+79991234567',
         'alex@mail.ru'),

        ('Мария Петрова',
         '+79997654321',
         'maria@mail.ru'),

        ('Дмитрий Сидоров',
         '+79998887766',
         'dima@mail.ru'),

        ('Елена Смирнова',
         '+79995554433',
         'elena@mail.ru'),

        ('Игорь Волков',
         '+79991112233',
         'igor@mail.ru')
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO clients
        (full_name, phone, email)
        VALUES (?, ?, ?)
    ''', clients)

    # =========================
    # Получаем id клиентов
    # =========================

    cursor.execute('SELECT id, full_name FROM clients')

    clients_dict = {
        name: id for id, name in cursor.fetchall()
    }

    # =========================
    # Получаем id экскурсий
    # =========================

    cursor.execute('SELECT id, title FROM excursions')

    excursions_dict = {
        title: id for id, title in cursor.fetchall()
    }

    # =========================
    # Добавляем бронирования
    # =========================

    bookings = [
        (
            clients_dict['Александр Иванов'],
            excursions_dict['Обзорная экскурсия'],
            '2026-05-10',
            2
        ),

        (
            clients_dict['Мария Петрова'],
            excursions_dict['Ночной Петербург'],
            '2026-05-11',
            4
        ),

        (
            clients_dict['Дмитрий Сидоров'],
            excursions_dict['Исторический центр'],
            '2026-05-12',
            1
        ),

        (
            clients_dict['Елена Смирнова'],
            excursions_dict['Горы Кавказа'],
            '2026-05-13',
            3
        ),

        (
            clients_dict['Игорь Волков'],
            excursions_dict['Золотое кольцо'],
            '2026-05-14',
            2
        )
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO bookings
        (client_id, excursion_id, booking_date, people_count)
        VALUES (?, ?, ?, ?)
    ''', bookings)

    conn.commit()

    # =========================
    # Проверка создания БД
    # =========================

    print("Файл БД создан:",
          os.path.exists('excursion.db'))

    # =========================
    # Статистика
    # =========================

    cursor.execute("SELECT COUNT(*) FROM guides")
    guides_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM excursions")
    excursions_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM clients")
    clients_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    bookings_count = cursor.fetchone()[0]

    print("\nБаза данных создана успешно!")

    print(f"Гидов: {guides_count}")
    print(f"Экскурсий: {excursions_count}")
    print(f"Клиентов: {clients_count}")
    print(f"Бронирований: {bookings_count}")

    conn.close()


if __name__ == '__main__':
    main()