# CacheCow

Simple Flask shop demo with SQLAlchemy models. It defaults to SQLite so a fresh clone runs without extra setup.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000. On first run, the app creates a local `cachecow.db` SQLite file and seeds demo data (including an admin user `admin@example.com` / `admin123`).

## Using MySQL instead

If you want MySQL, create the database and user:

```sql
CREATE DATABASE IF NOT EXISTS CacheCow;
CREATE USER IF NOT EXISTS 'cachecow_app'@'localhost' IDENTIFIED BY 'cachecow_dev';
GRANT ALL PRIVILEGES ON CacheCow.* TO 'cachecow_app'@'localhost';
FLUSH PRIVILEGES;
```

Then set `DATABASE_URL` in `.env` (or your environment):

```
DATABASE_URL=mysql+pymysql://cachecow_app:cachecow_dev@localhost:3306/CacheCow
```

Load the schema/data if you prefer the SQL files:

```bash
mysql -u cachecow_app -pcachecow_dev CacheCow < schema_mysql.sql
mysql -u cachecow_app -pcachecow_dev CacheCow < sample_data_mysql_pcparts.sql
```

## Environment

- `.env` is loaded automatically (see `.env` for defaults).
- `SQLALCHEMY_DATABASE_URI` comes from `DATABASE_URL` if set; otherwise falls back to SQLite at `cachecow.db`.
