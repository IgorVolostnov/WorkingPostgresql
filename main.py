import logging
from dotenv import load_dotenv
from work_base import PostgresBase

logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':
    load_dotenv()
    example_base = PostgresBase()
    example_base.connect()
