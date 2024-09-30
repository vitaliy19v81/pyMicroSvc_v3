# Используем Python как базовый образ
FROM python:3.10-slim

# Установка рабочего каталога
WORKDIR /wdir

# Копируем файл зависимостей в рабочий каталог
COPY app/requirements.txt ./requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r ./requirements.txt

# Копируем все файлы приложения
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]