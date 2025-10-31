import os
import psycopg2
from psycopg2 import Error


class PostgresBase:
    def __init__(self):
        self.user_base = os.getenv('user_base')
        self.password_base = os.getenv('password_base')
        self.host_base = os.getenv('host_base')
        self.port_base = os.getenv('port_base')
        self.name_database = os.getenv('name_database')
        self.connection = None
        self.cursor = None

    def check_connection(self):
        try:
            with psycopg2.connect(user=self.user_base, password=self.password_base,
                                  host=self.host_base, port=self.port_base,
                                  database=self.name_database) as self.connection:
                self.execute_check_connection()
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print("Соединение с PostgreSQL закрыто")

    def execute_check_connection(self):
        self.cursor = self.connection.cursor()
        print("Информация о сервере PostgreSQL")
        print(self.connection.get_dsn_parameters(), "\n")
        self.cursor.execute("SELECT version();")
        record = self.cursor.fetchone()
        print("Вы подключены к - ", record, "\n")

    def create_table(self):
        try:
            with psycopg2.connect(user=self.user_base, password=self.password_base,
                                  host=self.host_base, port=self.port_base,
                                  database=self.name_database) as self.connection:
                self.execute_create_table()
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print("Соединение с PostgreSQL закрыто")

    def execute_create_table(self):
        self.cursor = self.connection.cursor()
        # SQL-запрос для создания новой таблицы
        create_table_query = '''CREATE TABLE cameranorm (
        ID           SERIAL PRIMARY KEY,
        article      TEXT DEFAULT '', -- Артикул
        title        TEXT DEFAULT '', -- Наименование
        description  TEXT DEFAULT '', -- Описание
        current_retail       DECIMAL(14, 2) DEFAULT '0', -- Текущая розничная цена
        current_dealer       DECIMAL(14, 2) DEFAULT '0', -- Текущая оптовая цена
        old_retail       DECIMAL(14, 2) DEFAULT '0', -- Предыдущая розничная цена
        old_dealer       DECIMAL(14, 2) DEFAULT '0', -- Предыдущая оптовая цена
        availability DECIMAL(14, 2) DEFAULT '0', -- Наличие
        price_list   TEXT DEFAULT 'Нет в прайсах', -- Наименование прайс-листа
        grp          TEXT DEFAULT 'Нет в группах', -- Наименование группы
        photo        TEXT DEFAULT '', -- Фото на сайте
        link         TEXT DEFAULT '', -- Ссылка на сайте
        brand        TEXT DEFAULT 'NORM', -- Бренд
        date_update  TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Значение текущего времени по умолчанию
        source       TEXT DEFAULT 'cameranorm', -- Название источника
        type_change  TEXT DEFAULT 'Новый товар' -- тип изменения (Новый товар - при создании новой позиции)
        ); '''
        rename_table_query = '''ALTER TABLE norm_original RENAME TO cameranorm; '''
        delete_table_query = '''DELETE FROM analog; '''
        update_table_query = '''UPDATE cameranorm SET source = 'cameranorm'; '''
        self.cursor.execute(create_table_query)
        self.connection.commit()
        print(f"Таблица: norm успешно создана в PostgreSQL")

    def create_table_analog(self):
        try:
            with psycopg2.connect(user=self.user_base, password=self.password_base,
                                  host=self.host_base, port=self.port_base,
                                  database=self.name_database) as self.connection:
                self.execute_create_table_analog()
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if self.connection:
                self.cursor.close()
                self.connection.close()
                print("Соединение с PostgreSQL закрыто")

    def execute_create_table_analog(self):
        self.cursor = self.connection.cursor()
        # SQL-запрос для создания новой таблицы analog
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS analog (
                id SERIAL PRIMARY KEY,
                article VARCHAR(256),
                brand VARCHAR(256),
                article_cross VARCHAR(256),
                brand_cross VARCHAR(256),
                source VARCHAR(256),
                composite_key TEXT UNIQUE
            );

            -- Индекс по уникальному полю composite_key
            CREATE INDEX idx_composite_key ON analog(composite_key);
            '''

        self.cursor.execute(create_table_query)
        self.connection.commit()
        print(f"Таблица: analog успешно создана в PostgreSQL")
