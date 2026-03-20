Ubuntu 22.04.

markdown
# Gate.io Arbitrage Robot

Автоматизированная система для мониторинга и анализа арбитражных возможностей между спотовым и фьючерсным рынками **Gate.io**. Проект позволяет отслеживать крупные сделки, вычислять базис (спред) и визуализировать данные в реальном времени через веб-дашборд.

## Возможности

- 🔍 Сбор данных о сделках (спот и фьючерсы) через **REST API Gate.io**.
- 📊 Детектирование крупных сделок на основе скользящего среднего объёма.
- 📈 Расчёт базиса (разница между ценой фьючерса и спота) и его статистических характеристик.
- 🌐 Веб-интерфейс на чистом HTML/JS с графиками (Chart.js) и таблицей крупных сделок.
- ⚙️ Возможность смены торговой пары через интерфейс (настройки сохраняются в БД).
- 🗄️ Хранение данных в **SQLite** (по умолчанию) или **PostgreSQL**.

## Архитектура

- **Backend** – FastAPI приложение, предоставляющее REST API для фронтенда и взаимодействия с БД.
- **Collector** – отдельный Python-процесс, который периодически опрашивает публичные эндпоинты Gate.io и сохраняет сделки.
- **Frontend** – статические файлы (HTML, CSS, JS), общающиеся с API через fetch.
- **Database** – SQLite (файл `arbitrage.db`) для простоты развёртывания.

## Установка на Ubuntu 22.04

### 1. Подготовка системы

Обновите пакеты и установите необходимые инструменты:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
2. Получение проекта
Склонируйте репозиторий (или скопируйте файлы вручную):

bash
git clone https://github.com/yourusername/gateio-arbitrage.git
cd gateio-arbitrage
Если вы используете скрипт генерации generate.py (создаёт все файлы автоматически), запустите его:

bash
python3 generate.py
3. Настройка виртуального окружения и зависимостей
bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Файл requirements.txt включает:

text
fastapi
uvicorn[standard]
requests
numpy
python-dotenv
sqlalchemy
4. Инициализация базы данных
bash
python3 init_db.py
Эта команда создаст таблицы и добавит начальные настройки (по умолчанию BTC_USDT, порог 2.5σ, окно базиса 60 минут).

5. Запуск компонентов
Запуск бэкенда (FastAPI)
bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
API будет доступно по адресу http://<IP-сервера>:8000.

Запуск коллектора
Откройте новый терминал и выполните:

bash
cd collector
python3 collector.py
Коллектор начнёт собирать данные с Gate.io (опрос каждые 2 секунды).

Запуск фронтенда
Фронтенд — статические файлы. Для быстрого запуска используйте встроенный HTTP-сервер Python:

bash
cd frontend
python3 -m http.server 8080
Теперь дашборд доступен по адресу http://<IP-сервера>:8080.

6. Настройка автозапуска (опционально, для продакшена)
Для автоматического запуска при старте системы рекомендуется создать systemd-сервисы.

Сервис для API
Создайте файл /etc/systemd/system/arbitrage-api.service:

ini
[Unit]
Description=Arbitrage API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gateio-earbitrag/backend
Environment="PATH=/home/ubuntu/gateio-arbitrage/venv/bin"
ExecStart=/home/ubuntu/gateio-arbitrage/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
Сервис для коллектора
Файл /etc/systemd/system/arbitrage-collector.service:

ini
[Unit]
Description=Arbitrage Collector
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gateio-arbitrage/collector
Environment="PATH=/home/ubuntu/gateio-arbitrage/venv/bin"
ExecStart=/home/ubuntu/gateio-arbitrage/venv/bin/python collector.py
Restart=always

[Install]
WantedBy=multi-user.target
После создания файлов выполните:

bash
sudo systemctl daemon-reload
sudo systemctl enable arbitrage-api arbitrage-collector
sudo systemctl start arbitrage-api arbitrage-collector
7. Настройка обратного прокси с Nginx (рекомендуется)
Установите Nginx:

bash
sudo apt install -y nginx
Создайте конфигурацию сайта /etc/nginx/sites-available/arbitrage:

nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        root /home/ubuntu/gateio-arbitrage/frontend;
        index index.html;
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
Активируйте сайт:

bash
sudo ln -s /etc/nginx/sites-available/arbitrage /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
Теперь дашборд доступен по стандартному HTTP-порту 80 (без указания порта).

Использование
Откройте веб-интерфейс (например, http://your-server-ip).

Выберите торговую пару из выпадающего списка (BTC_USDT, ETH_USDT и др.) и нажмите «Сохранить».

Коллектор автоматически переключится на новую пару (максимальная задержка – до 20 секунд).

На графиках отобразятся цены спота и фьючерса, а также базис (в процентах) с доверительными интервалами (±1σ).

Крупные сделки (превышающие порог) будут отмечены на графике цен и в таблице снизу.

Настройка параметров
Параметры хранятся в таблице config базы данных. Их можно изменить через API (эндпоинт /api/config) или напрямую в БД.

Пример изменения порога крупной сделки через curl:

bash
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"volume_threshold_std": "3.0"}'
Доступные ключи:

current_pair – текущая торговая пара.

volume_threshold_std – количество стандартных отклонений для определения крупной сделки.

basis_mean_window – окно (в минутах) для расчёта среднего базиса.

Переход на PostgreSQL (опционально)
Установите PostgreSQL:

bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
Создайте базу и пользователя:

bash
sudo -u postgres psql
CREATE DATABASE arbitrage;
CREATE USER arbuser WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE arbitrage TO arbuser;
\q
В файле .env измените DATABASE_URL:

text
DATABASE_URL=postgresql://arbuser:securepassword@localhost/arbitrage
Пересоздайте таблицы (если ранее использовали SQLite, удалите старый файл или начните с чистой БД).

Требования
Python 3.8+

Доступ к интернету для опроса API Gate.io.

1 ГБ RAM (минимум), 2 ГБ рекомендуется для хранения истории сделок.

Лицензия
MIT

Авторы
Разработано в рамках исследования арбитражных стратегий на криптовалютных рынках.

text

Этот README содержит все необходимые шаги для развёртывания проекта на Ubuntu 22.04. Если потребуется добавить раздел про отладку или типичные ошибки, дайте знать.

