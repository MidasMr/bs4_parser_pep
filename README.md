# Проект парсинга pep

### Описание проетка:

Это учебный проект парсера, который считает количество PEP в общем и в частности по каждому статусу.

### Установка:

Клонировать репозиторий и перейти в него:

```
git@github.com:MidasMr/bs4_parser_pep.git
```

```
cd bs4_parser_pep
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```


Windows
```
source venv/Scripts/activate
```

Linux, Mac OS
```
source venv/bin/activate
```

```
Обновить pip до последней версии

python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Для запуска нужно перейти в директорию со скриптами:
```
cd src
```

После этого можно выполнять следующие команды:

Получить список всех команд:
```
python main.py -h
```

Получить информацию об обновлениях:
```
python main.py whats-new
```

Получить информацию о последних версиях Python:
```
python main.py latest-versions
```

Скачать документацию:
```
python main.py download
```
Файл появится в директории ``` src/downloads ```

Получить информацию об общем количестве PEP и о количестве в каждом статусе:
```
python main.py pep
```

режимы вывода:

отобразить таблицей в терминале
```
-o pretty
```

экспортировать в виде файла csv
```
-o file
```
Файл появится в директории ``` src/results ```


Стек технологий:
```
Python 3.9
beautifulsoup4
```



Автор:
[Александр Вязников(MidasMr)](https://github.com/MidasMr)
