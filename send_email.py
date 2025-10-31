import os
import json
from pathlib import Path
from email.header import Header
from email.encoders import encode_base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from typing import List, Optional
from aiosmtplib import SMTP


class EmailSender:
    """
    Класс для асинхронной отправки электронных писем через почтового провайдера **Mail.Ru**.

    Атрибуты:
        • from_email (str): e-mail отправителя.
        • password (str): пароль от аккаунта отправителя.
        • to_emails (list of str): список e-mail получателей.

    Методы:
        • send_mail (subject_letter: str, message_text: str, file_path: Optional[str] = None): асинхронный метод отправки электронного письма.

   Примечание:
       Для повышения безопасности рекомендуется хранить учетные данные и адреса
       получателей в файле **.env** и загружать их через переменные окружения.
   """
    def __init__(self,
                 from_email: Optional[str] = None,
                 password: Optional[str] = None,
                 to_emails: Optional[List[str]] = None
                 ) -> None:
        """
        Инициализация объекта класса `EmailSender`.

        :param from_email: e-mail отправителя. По умолчанию берется из переменной окружения `FROM_EMAIL`.
        :param password: пароль от аккаунта отправителя. По умолчанию берется из переменной окружения `EMAIL_PASSWORD`.
        :param to_emails: список адресов получателей в формате JSON-списка. Если параметр не задан — значение берётся из переменной окружения `TO_EMAILS`.
        """
        self.from_email = from_email or os.getenv('FROM_EMAIL')
        self.password = password or os.getenv('EMAIL_PASSWORD')
        to_emails_str = to_emails or os.getenv('TO_EMAILS', '[]')
        self.to_emails = json.loads(to_emails_str)

    async def send_mail(self,
                        subject_letter: str,
                        message_text: str,
                        file_path: Optional[str] = None
                        ):
        """
        Асинхронный метод отправки электронного письма.

        :param subject_letter: тема письма.
        :param message_text: текст тела письма в HTML-разметке.
        :param file_path: путь до файла для вложения в письмо (если есть). Необязательный аргумент.

        :raises Exception: возникает, если письмо не отправлено.

        Пример использования:
            sender = EmailSender(from_email="example@mail.ru", password="password123",
            to_emails=["recipient@example.com"])

            await sender.send_mail("Тема письма", "<h1>Привет!</h1>")
        """
        message = MIMEMultipart()
        message['From'] = self.from_email
        message['To'] = ', '.join(self.to_emails)
        message['Subject'] = subject_letter

        html_content = f'<html><body>{message_text}</body></html>'
        message.attach(MIMEText(html_content, 'html', 'utf-8'))

        if file_path:
            attachment_name = Path(file_path).name

            content_type_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.csv': 'text/csv',
                '.txt': 'text/plain',
                '.jpg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed'
            }
            content_type = content_type_map.get(Path(file_path).suffix.lower(), 'application/octet-stream')

            with open(file_path, "rb") as file:
                main_type, sub_type = content_type.split('/', 1)
                part = MIMEBase(main_type, sub_type)
                part.set_payload(file.read())
                encode_base64(part)
                header_value = Header(attachment_name, charset='UTF-8').encode()
                part.add_header('Content-Disposition', 'attachment', filename=header_value)
                message.attach(part)
        try:
            smtp_client = SMTP(hostname='smtp.mail.ru', port=465, use_tls=True)

            async with smtp_client:
                await smtp_client.login(self.from_email, self.password)
                await smtp_client.send_message(message)

        except Exception as e:
            print(f'Произошла ошибка при отправке письма: {str(e)}')
