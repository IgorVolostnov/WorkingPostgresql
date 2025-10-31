import asyncio
import logging
from dotenv import load_dotenv
from send_email import EmailSender

logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':
    load_dotenv()
    email_sender = EmailSender()
    asyncio.run(email_sender.send_mail(
        subject_letter="Изменившиеся позиции товаров NORM",
        message_text='''<h2>Добрый день! Приложены товары, у которых произошли изменения по бренду NORM.</h2>'''
                     '''<h3>С уважением,<br /> Волостнов Игорь</h3>'''
                     '''<p>Московское представительство &laquo;Россвик&raquo;<br /> ООО &laquo;Алькар&raquo;</p>'''
                     '''<p>+7-977-900-7773 сотовый<br /> 
                     +7-495-215-0003 многоканальный<br /> 
                     +7-800-333-2260 бесплатные звонки по России</p>'''
                     '''<p>Офис: 127562, Москва, ул. Хачатуряна, д. 8, к. 3, комн. 15<br /> 
                     Склад: 141017, Мытищи, ул. 1-ая Новая, д. 57 (Координаты: 55.949229, 37.784479)</p>'''
                     '''<p>E-mail: <a href="mailto:iv@rossvik.moscow">iv@rossvik.moscow</a></p>'''
                     '''<p>Telegram-канал: <a href="https://t.me/rossvik_moscow">https://t.me/rossvik_moscow</a></p>'''
                     '''<p>Сайт: <a href="www.rossvik.moscow">www.rossvik.moscow</a></p>'''
                     '''<p><img src="https://www.rossvik.moscow/images/logo_1920_new.png" 
                     alt="Logo" width="400" height="43" /></p>''',
        file_path="C:\\Users\\IV\\Desktop\\Прайсы\\Прайсы по наличию\\Формирование прайсов\\Прайсы с ценами\\Прайсы Россвик\\Вулканизаторы Россвик дилерский прайс от 31.10.2025.xlsx"))
