#!/usr/bin/env python3
import cgi
import os
from datetime import datetime
import subprocess
from typing import Tuple, Optional


# Константы
HTML_DIR = "/var/www/webapp/html"
ORIGINAL_DIR = "/var/www/webapp/original"
CONVERTED_DIR = "/var/www/webapp/converted"
RESULT_PAGE = os.path.join(HTML_DIR, "result.html")
ERROR_PAGE = os.path.join(HTML_DIR, "error.html")


class ImageProcessor:
    """
    Класс для обработки загрузки и конвертации изображений.
    """

    def __init__(self):
        self.form = cgi.FieldStorage()

    def save_upload(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Сохраняет загруженное изображение в папку оригиналов.
        Возвращает путь к оригиналу, уникальное имя файла или ошибку.
        """
        if 'image' not in self.form:
            return None, None, "No file uploaded"

        file_item = self.form['image']
        if not file_item.filename:
            return None, None, "No filename provided"

        content_type = file_item.type
        if content_type not in ['image/jpeg', 'image/png']:
            return None, None, "Invalid file type"

        # Генерация уникального имени
        unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.getpid()}"
        ext = ".jpg" if content_type == 'image/jpeg' else ".png"
        unique_name += ext

        original_path = os.path.join(ORIGINAL_DIR, unique_name)

        try:
            with open(original_path, 'wb') as f:
                f.write(file_item.file.read())
        except Exception as e:
            return None, None, f"File write error: {e}"

        return original_path, unique_name, None

    def convert_image(self, input_path: str, output_path: str) -> bool:
        """
        Конвертирует изображение в градации серого с помощью ImageMagick.
        """
        try:
            subprocess.run(['convert', input_path, '-colorspace', 'Gray', output_path], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"<!-- Conversion error: {e} -->")
            return False

    def render_template(self, template_path: str, filename: Optional[str] = None) -> str:
        """
        Загружает HTML-шаблон и заменяет плейсхолдер {{filename}} на имя файла.
        """
        try:
            with open(template_path, 'r') as f:
                content = f.read()
            if filename:
                content = content.replace("{{filename}}", filename)
            return content
        except Exception as e:
            print(f"<!-- Template rendering error: {e} -->")
            return "<h1>Internal Server Error</h1>"


def main():
    print("Content-Type: text/html\n")

    try:
        processor = ImageProcessor()
        original_path, unique_name, error = processor.save_upload()

        if error:
            with open(ERROR_PAGE) as f:
                print(f.read())
            return

        converted_path = os.path.join(CONVERTED_DIR, unique_name)

        if not processor.convert_image(original_path, converted_path):
            with open(ERROR_PAGE) as f:
                print(f.read())
            return

        result_html = processor.render_template(RESULT_PAGE, unique_name)
        print(result_html)

    except Exception as e:
        # Любая неожиданная ошибка → показываем error.html
        print("Content-Type: text/html\n")
        try:
            with open(ERROR_PAGE) as f:
                print(f.read())
        except Exception:
            print("<h1>Internal Server Error</h1>")
            print("<p>Could not load error page.</p>")


if __name__ == '__main__':
    main()
