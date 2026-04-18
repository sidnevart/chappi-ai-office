---
sidebar_position: 10
title: Star Office UI и Grafana
---

# Настройка дашбордов

## Star Office UI (порт 3000)

### Установка

```bash
ssh root@ВАШ_IP

# Клонировать репозиторий
git clone https://github.com/ringhyacinth/Star-Office-UI /opt/ai-office/star-office

# Установить зависимости Python
/opt/ai-office/mempalace-venv/bin/pip install flask psycopg2-binary

# Скопировать файл маршрутов для AI Office
# (файл ai_office_routes.py из этого репозитория)
```

### Настройка маршрутов AI Office

Скопируйте `ai_office/vps/star-office/ai_office_routes.py` на сервер:

```bash
scp ai_office/vps/star-office/ai_office_routes.py \
  root@ВАШ_IP:/opt/ai-office/star-office/backend/ai_office_routes.py
```

Добавьте в `/opt/ai-office/star-office/backend/app.py` после других импортов:

```python
from ai_office_routes import ai_office_bp
app.register_blueprint(ai_office_bp)
```

### Systemd-служба

Создайте `/etc/systemd/system/ai-office-ui.service`:

```ini
[Unit]
Description=AI Office Star-Office-UI
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ai-office/star-office/backend
ExecStart=/opt/ai-office/mempalace-venv/bin/python3 app.py
Restart=on-failure
RestartSec=5
Environment=FLASK_ENV=production
Environment=FLASK_SECRET_KEY=придумайте-надёжный-ключ
Environment=STAR_OFFICE_SECRET=придумайте-надёжный-ключ
Environment=ASSET_DRAWER_PASS=придумайте-надёжный-пароль
Environment=OPENCLAW_WORKSPACE=/root/.openclaw/workspace
Environment=POSTGRES_HOST=localhost
Environment=POSTGRES_PORT=5432
Environment=POSTGRES_DB=ai_office
Environment=POSTGRES_USER=postgres
Environment=POSTGRES_PASSWORD=ВАШ_ПАРОЛЬ
Environment=STAR_BACKEND_PORT=3000

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable ai-office-ui
systemctl start ai-office-ui
```

---

## Grafana (порт 4000)

### Запуск

```bash
docker run -d \
  --name ai-office-grafana \
  --restart unless-stopped \
  -p 4000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=придумайте-пароль \
  -e GF_SERVER_HTTP_PORT=3000 \
  -v grafana-data:/var/lib/grafana \
  grafana/grafana-oss:latest
```

### Добавление источника данных PostgreSQL

1. Войдите на [http://ВАШ_IP:4000](http://ВАШ_IP:4000) (логин: `admin`)
2. Перейдите в **Connections → Data Sources → Add data source**
3. Выберите **PostgreSQL**
4. Заполните:
   - Host: `localhost:5432`
   - Database: `ai_office`
   - User: `postgres`
   - Password: ваш пароль
   - TLS/SSL Mode: `disable`

### Создание дашборда

Импортируйте JSON дашборда из `ai_office/vps/grafana/dashboard.json` через **Dashboards → Import**.

Или создайте вручную панели с запросами к таблице `event_log`:

```sql
-- Активность по часам
SELECT date_trunc('hour', created_at) AS time, count(*) AS actions
FROM event_log
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1 ORDER BY 1;
```
