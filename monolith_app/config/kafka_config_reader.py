# config/kafka_config_reader.py

def read_kafka_config(file_path, key):
    """
    Читает значение указанного ключа из файла server.properties.

    :param file_path: Путь к файлу server.properties
    :param key: Ключ для извлечения значения
    :return: Значение ключа в виде строки или None, если ключ не найден
    """
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Пропускаем комментарии и пустые строки
                if line.startswith('#') or not line.strip():
                    continue
                # Разделяем строку на ключ и значение
                parts = line.split('=')
                if parts[0].strip() == key:
                    return parts[1].strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {file_path} не найден.")
    except Exception as e:
        raise Exception(f"Ошибка при чтении файла {file_path}: {e}")

    return None
