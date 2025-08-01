# RAO — установка и запуск на Windows 7 SP1 x64

## 📦 Требования

Перед установкой убедитесь, что на компьютере установлены:

1. **Python 3.8.2 x64 (последняя версия с поддержкой Windows 7)**
   - Скачать: [python-3.8.2-amd64.exe](https://www.python.org/ftp/python/3.8.2/python-3.8.2-amd64.exe)
   - ⚠️ Более новые версии Python (3.9 и выше) не работают на Windows 7
   - При установке обязательно:
     - Отметить галочку **"Add Python to PATH"**
     - Выбрать **"Install for all users"** (если есть права администратора)


2. **Git for Windows (версия для Windows 7)**  
   - Скачать: [https://github.com/git-for-windows/git/releases/tag/v2.34.1.windows.1](https://github.com/git-for-windows/git/releases/tag/v2.34.1.windows.1)  
   - Установить с настройками по умолчанию

---

## 🔧 Установка

1. Откройте проводник и перейдите в папку, куда хотите установить программу.


2. Кликните правой кнопкой мыши в этой папке и выберите  
   **"Git Bash Here"** или **"Открыть окно команд"**.


3. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/BLXNK-333/rao.git
   ```

4. Перейдите в папку проекта:
   ```bash
   cd rao
   ```

5. Запустите установочный скрипт:
   
   ```bash
   python setup.py
   ```
   
   Этот скрипт:
   
   * Проверит установлен ли Python
   * Создаст виртуальное окружение `.venv`
   * Установит все зависимости
   * Создаст ярлык на рабочем столе для запуска программы

---

## 🚀 Запуск программы

Просто дважды щёлкните по ярлыку **РАО**, который появится на рабочем столе.

---

## 🔄 Обновление

Чтобы обновить программу до последней версии:

1. Перейдите в папку проекта:
   ```bash
   cd C:\PythonProjects\rao
   ```
   
2. Выполните команду:
   ```bash
   python update.py
   ```

Скрипт автоматически загрузит обновления и обновит зависимости.

---

## 🧹 Удаление

Если вы больше не планируете использовать программу:

1. (По желанию) Сделайте копию файла базы данных `rao.db`, если хотите сохранить данные

2. Удалите папку проекта (ту, куда клонировали репозиторий)

3. Удалите ярлык с рабочего стола
