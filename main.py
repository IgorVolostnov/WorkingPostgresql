import logging
from dotenv import load_dotenv
from work_base import PostgresBase

logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':
    load_dotenv()
    example_base = PostgresBase()
    # example_base.connect()
    # example_base.view_all_table()
    # example_base.view_info_about_table('synonyms')
    # example_base.delete_table('synonyms')
    # example_base.view_search_configuration()
    # example_base.delete_search_configuration('my_russian_copy')
    # example_base.create_search_configuration('my_search_conf', 'russian')
    # example_base.create_search_synonym('synonyms')
    # example_base.delete_record('synonyms')
    # example_base.update_search_synonym()
    # example_base.view_last_10_record('synonyms')
    # example_base.create_change_synonym_function()
    # example_base.view_all_function_sql()
    example_base.search_record_table('cameranorm', ['чупачупс'])
