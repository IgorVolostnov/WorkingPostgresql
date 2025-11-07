import os
from typing import Optional
import asyncio
import psycopg2
from send_email import EmailSender


class PostgresBase:
    """
    Базовый класс для взаимодействия с базой данных **PostgreSQL**.

    Атрибуты:
        • user_base (str): имя пользователя базы данных.
        • password_base (str): пароль пользователя базы данных.
        • host_base (str): адрес хоста базы данных.
        • port_base (str): порт базы данных.
        • name_database (str): название базы данных.
        • email_sender (EmailSender): экземпляр класса для отправки уведомлений об ошибках по электронной почте.

    Методы:
        • __init__(...): конструктор класса.
        • _send_email(...): внутренний метод для отправки уведомления по ошибке.
        • connect(): проверяет подключение к базе данных.
        • create_table(name_table: str, name_brand: str): создает таблицу в базе данных.

    Примечание:
       Для повышения безопасности рекомендуется хранить учетные данные подключения
       к базе данных в файле **.env** и загружать их через переменные окружения.
    """

    def __init__(self,
                 user_base: Optional[str] = None,
                 password_base: Optional[str] = None,
                 host_base: Optional[str] = None,
                 port_base: Optional[str] = None,
                 name_database: Optional[str] = None) -> None:
        """
        Инициализирует объект класса `PostgresBase` с параметрами подключения к базе данных.

        :param user_base: имя пользователя базы данных.
        :param password_base: пароль пользователя базы данных.
        :param host_base: адрес хоста базы данных.
        :param port_base: порт базы данных.
        :param name_database: название базы данных.

        Если аргумент отсутствует, берется значение из переменных среды окружения.
        """
        self.user_base = user_base or os.getenv('USER_BASE')
        self.password_base = password_base or os.getenv('PASSWORD_BASE')
        self.host_base = host_base or os.getenv('HOST_BASE')
        self.port_base = port_base or os.getenv('PORT_BASE')
        self.name_database = name_database or os.getenv('NAME_DATABASE')
        self.email_sender = EmailSender()

    async def _send_email(self, name_class: str, name_method: str, description_error: str):
        """
        Отправляет уведомление об ошибке.

        :param name_class: имя класса, где произошла ошибка.
        :param name_method: имя метода класса, где произошла ошибка.
        :param description_error: описание ошибки.
        """
        await self.email_sender.send_mail(
            subject_letter=f"Произошла ошибка в классе {name_class}, в методе {name_method}",
            message_text=f'''<h2>Описание ошибки: {description_error}</h2>''')

    def connect(self):
        """
        Проверяет подключение к базе данных **PostgreSQL**.

        В случае возникновения ошибки отправляет уведомление по электронной почте.
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database) as conn:
                cur = conn.cursor()
                cur.execute("SELECT version()")
                result = cur.fetchone()[0]
                print(f"Выполнено подключение к PostgreSQL версии: {result}")
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "connect", str(e)))

    def create_table(self, name_table: str, name_brand: str):
        """
        Создаёт новую таблицу в базе данных.

        :param name_table: имя создаваемой таблицы.
        :param name_brand: наименование бренда товара.

        Таблица содержит поля для хранения артикула, названия, описания, цен, наличия товаров и другие метаданные.
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {name_table} (
            id SERIAL PRIMARY KEY,
            article TEXT DEFAULT '',
            title TEXT DEFAULT '',
            description TEXT DEFAULT '',
            current_retail DECIMAL(14, 2) DEFAULT '0',
            current_dealer DECIMAL(14, 2) DEFAULT '0',
            old_retail DECIMAL(14, 2) DEFAULT '0',
            old_dealer DECIMAL(14, 2) DEFAULT '0',
            availability DECIMAL(14, 2) DEFAULT '0',
            price_list TEXT DEFAULT 'Нет в прайсах',
            grp TEXT DEFAULT 'Нет в группах',
            photo TEXT DEFAULT '',
            link TEXT DEFAULT '',
            brand TEXT DEFAULT '{name_brand}',
            date_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT '{name_table}',
            type_change TEXT DEFAULT 'Новый товар'
        );
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database) as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "create_table", str(e)))

    def create_table_analog(self):
        """
        Создаёт таблицу кроссов по товарам различных брендов в базе данных.

        Таблица содержит поля для хранения артикула, бренда, артикула кросса, бренда кросса, источника кросса,
        а также составной ключ и индекс по нему для поиска.
        """
        query = f"""
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
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database) as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "create_table_analog", str(e)))

    def rename_table(self, old_name: str, new_name: str):
        """
        Переименовывает таблицу в базе данных.

        :param old_name: текущее имя таблицы в базе данных.
        :param new_name: новое имя таблицы в базе данных.
        """
        query = f"""
        ALTER TABLE {old_name} RENAME TO {new_name};
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database) as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "rename_table", str(e)))

    def delete_table(self, name_table: str):
        """
        Удаляет таблицу из базы данных.

        :param name_table: имя таблицы для удаления из базы данных.
        """
        query = f"""
        DELETE FROM {name_table};
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database) as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "delete_table", str(e)))

    def update_all_row_field_table(self, name_table: str, name_field: str, value_field: str):
        """
        Обновляет значение поля по всем записям таблицы.

        :param name_table: имя таблицы для обновления.
        :param name_field: имя поля, все значения которого необходимо обновить.
        :param value_field: значение, которое примут все записи таблицы по заданному полю.
        """
        query = f"""
        UPDATE {name_table} SET {name_field} = '{value_field}';
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database) as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "update_all_row_field_table", str(e)))
