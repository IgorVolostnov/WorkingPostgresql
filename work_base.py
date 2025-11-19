from __future__ import annotations
import os
from typing import Optional, List
import asyncio
import psycopg2
from send_email import EmailSender
from prettytable import PrettyTable


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
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute("SELECT version()")
                result = cur.fetchone()[0]
                print(f"Выполнено подключение к PostgreSQL версии: {result}")
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "connect", str(e)))

    def view_all_table(self):
        """
        Показывает все таблицы в базе данных.
        """
        query = """
            SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                result = cur.fetchall()
                for item in result:
                    print(item)
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "view_all_table", str(e)))

    def view_info_about_table(self, name_table: str):
        """
        Показывает подробную информацию о заданной таблице.

        :param name_table: имя создаваемой таблицы.
        """
        query = f"""
        SELECT
            a.attname AS имя_поля,
            a.attnum AS номер_столбца,
            format_type(a.atttypid, a.atttypmod) AS тип_данных,
            col_description(a.attrelid, a.attnum) AS комментарий,
            CASE WHEN a.attnotnull THEN 'NOT NULL' ELSE '' END AS обязательность,
            a.atthasdef AS имеет_значение_по_умолчанию,
            pg_catalog.pg_get_expr(d.adbin, d.adrelid) AS значение_по_умолчанию
        FROM
            pg_attribute a
        LEFT JOIN
            pg_attrdef d ON a.attrelid = d.adrelid AND a.attnum = d.adnum
        WHERE
            a.attrelid = %s::regclass
        AND
            a.attnum > 0
        AND
            NOT a.attisdropped
        ORDER BY
            a.attnum;
        """

        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query, (name_table,))
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                pt = PrettyTable(columns)
                for row in rows:
                    pt.add_row(row)
                print(pt.get_string())
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "view_info_about_table", str(e)))

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
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
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
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
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
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
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
        DROP TABLE IF EXISTS {name_table};
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
                print("Данные успешно удалены.")
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
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "update_all_row_field_table", str(e)))

    def view_search_configuration(self):
        """
        Показывает все доступные конфигурации полнотекстового поиска в базе данных.
        """
        query = """
            SELECT 
                cfgname, 
                prsname, 
                nsp.nspname AS namespace, 
                rol.rolname AS owner,
                string_agg((SELECT dictname FROM pg_ts_dict WHERE oid = cm.mapdict), ',') AS dictnames
            FROM pg_ts_config cfg
            JOIN pg_ts_parser par ON cfg.cfgparser = par.oid
            JOIN pg_namespace nsp ON cfg.cfgnamespace = nsp.oid
            JOIN pg_roles rol ON cfg.cfgowner = rol.oid
            LEFT JOIN pg_ts_config_map cm ON cfg.oid = cm.mapcfg
            GROUP BY cfgname, prsname, nsp.nspname, rol.rolname;
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                results = cur.fetchall()

                if len(results) == 0:
                    print("Конфигурации полнотекстового поиска не найдены.")
                    return

                table = PrettyTable()
                table.field_names = ["Название конфиг.", "Парсер", "Пространство имён", "Владелец", "Список словарей"]

                for row in results:
                    table.add_row([
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        row[4]
                    ])

                print(table)
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "view_search_configuration", str(e)))

    def delete_search_configuration(self, name_conf: str):
        """
        Удаляет конфигурацию полнотекстового поиска из базы данных.

        :param name_conf: имя конфигурации полнотекстового поиска для удаления из базы данных.
        """
        query = f"""
        DROP TEXT SEARCH CONFIGURATION IF EXISTS {name_conf};
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "delete_search_configuration", str(e)))

    def create_search_configuration(self, name_conf: str, start_conf: str):
        """
        Создает собственную конфигурацию полнотекстового поиска из базы данных на основе встроенной.

        :param name_conf: имя новой конфигурации полнотекстового поиска для создания в базе данных.
        :param start_conf: имя встроенной конфигурации полнотекстового поиска.
        """
        query = f"""
        CREATE TEXT SEARCH CONFIGURATION {name_conf} (COPY = {start_conf});
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "create_search_configuration", str(e)))

    def create_search_synonym(self, name_table_synonym: str):
        """
        Создаёт таблицу синонимов для полнотекстового поиска.

        :param name_table_synonym: имя новой таблицы синонимов для создания в базе данных.
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {name_table_synonym} (
            id SERIAL PRIMARY KEY,
            word TEXT NOT NULL,
            synonym TEXT UNIQUE NOT NULL,
            date_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            creator TEXT DEFAULT CURRENT_USER
            );
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "create_search_synonym", str(e)))

    def update_search_synonym(self):
        """
        Обновляет таблицу синонимов для полнотекстового поиска из текстового файла.
        """
        filename = "synonyms.txt"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл {filename} не найден!")

        with open(filepath, encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(maxsplit=1)
                if len(parts) != 2:
                    continue  # пропускаем некорректные строки
                new_word, new_synonym = parts

                query = """
                    INSERT INTO synonyms (
                        word, synonym
                    )
                    VALUES (
                        %(new_word)s, %(new_synonym)s
                    )
                    ON CONFLICT (synonym) DO UPDATE SET
                        word = EXCLUDED.word,
                        date_create = NOW();
                """

                # Подготовка параметров для безопасной передачи
                prepared_data = {
                    'new_word': new_word,
                    'new_synonym': new_synonym
                }

                try:
                    with psycopg2.connect(
                            user=self.user_base,
                            password=self.password_base,
                            host=self.host_base,
                            port=self.port_base,
                            database=self.name_database,
                            options="-c timezone=Europe/Moscow"
                    ) as conn:
                        cur = conn.cursor()
                        cur.execute(query, prepared_data)
                        conn.commit()
                except psycopg2.Error as e:
                    asyncio.run(self._send_email("PostgresBase", "update_search_synonym", str(e)))

    def view_all_function_sql(self):
        """
        Выводит список всех функций, хранящихся в базе данных с подробностями.
        """
        query = """
            SELECT routine_name, specific_name, data_type, routine_definition
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            ORDER BY routine_name;
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                results = cur.fetchall()

                table = PrettyTable()
                table.field_names = ["Имя функции", "Специфичное имя", "Возвращаемый тип", "Определение"]

                for row in results:
                    table.add_row(row)

                print(table)
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "view_all_function_sql", str(e)))

    def create_change_synonym_function(self):
        """
        Создает функцию, которая принимает строку запроса и заменяет слова, найденные в таблице синонимов,
        соответствующими синонимами.
        """
        query = """
            CREATE OR REPLACE FUNCTION replace_synonyms(query text) RETURNS text AS $$
            DECLARE
                result text := query;
                rec RECORD;
            BEGIN
                FOR rec IN (SELECT word, synonym FROM synonyms ORDER BY length(word) DESC) LOOP
                    result := regexp_replace(result, '\y' || rec.word || '\y', rec.synonym, 'gi');
                END LOOP;
                RETURN result;
            END;
            $$ LANGUAGE plpgsql;
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "create_change_synonym_function", str(e)))

    def search_record_table(self, name_table: str, search_arr: List[str]) -> list | str:
        """
        Ищет записи в указанной таблице по списку слов.

        :param name_table: Имя таблицы для поиска.
        :param search_arr: Список слов для поиска.
        :return: Список найденных записей или "undefined", если ничего не найдено.
        """
        if not isinstance(search_arr, list) or len(search_arr) == 0:
            return []

        search_query_string = " & ".join(search_arr)
        sql_query = f"""
        WITH search_query AS (
            SELECT replace_synonyms('{search_query_string}')::text AS search_term
        ),
        combined_search AS (
            SELECT
                *,
                ts_rank(
                    to_tsvector('my_search_conf', CONCAT(article, ' ', title, ' ', description)),
                    plainto_tsquery('my_search_conf', search_term)
                ) AS rank
            FROM {name_table}, search_query
            WHERE
                to_tsvector('my_search_conf', CONCAT(article, ' ', title, ' ', description))
                @@ plainto_tsquery('my_search_conf', search_term)
        )
        SELECT DISTINCT ON (id)
            article, title, brand, description, current_retail, current_dealer, availability, photo, link
        FROM combined_search
        ORDER BY id, rank DESC NULLS LAST;
        """

        records = None
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                records = cursor.fetchall()
                headers = [col.name for col in cursor.description]

                table = PrettyTable(headers)
                for record in records:
                    table.add_row(record)

                print(f'Найдены следующие позиции по поисковому запросу "{search_query_string}":')
                print(table)
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "search_record_table", str(e)))

        if not records:
            return "undefined"
        else:
            return records

    def view_last_10_record(self, name_table: str):
        """
        Показывает 10 последних записей в заданной таблице базы данных.

        :param name_table: имя таблицы для отображения последних 10 записей.
        """
        query = f"""
        SELECT * 
        FROM "{name_table}" 
        ORDER BY id DESC LIMIT 10"""
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                cur.execute(query)

                records = cur.fetchall()
                headers = [col.name for col in cur.description]

                table = PrettyTable(headers)
                for record in records:
                    table.add_row(record)

                print(f'\nПоследние 10 записей из таблицы "{name_table}":')
                print(table)
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "view_last_10_record", str(e)))

    def delete_record(self, name_table: str, id_record: int = None):
        """
        Удаляет запись из таблицы по id, если id не указан, то удаляет все записи из таблицы.

        :param name_table: имя таблицы в базе данных.
        :param id_record: номер записи в таблице для удаления.
        """
        try:
            with psycopg2.connect(user=self.user_base,
                                  password=self.password_base,
                                  host=self.host_base,
                                  port=self.port_base,
                                  database=self.name_database,
                                  options="-c timezone=Europe/Moscow") as conn:
                cur = conn.cursor()
                if id_record is not None:
                    query = f"DELETE FROM {name_table} WHERE id=%s;"
                    cur.execute(query, (id_record,))
                    print(f"Запись с ID={id_record} успешно удалена.")
                else:
                    query = f"DELETE FROM {name_table};"
                    cur.execute(query)
                    print("Все записи из таблицы успешно удалены.")
                conn.commit()
        except psycopg2.Error as e:
            asyncio.run(self._send_email("PostgresBase", "delete_record", str(e)))
