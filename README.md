# CareWhistle v78-lite

Your application is already production-ready for MySQL and MariaDB - just configure the connection details!

## Database configuration

The app supports multiple database backends. It will automatically connect to the first backend for which all required settings are present:

1. **PostgreSQL** – set `DATABASE_URL` to a valid connection string.
2. **MySQL** – set `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE`.
3. **MariaDB** – set `MARIADB_HOST`, `MARIADB_USER`, `MARIADB_PASSWORD`, and `MARIADB_DATABASE`.
4. **SQLite** – used as a fallback when no other backend is configured.

## Getting started

Install dependencies and run the development server:

```bash
pip install -r requirements.txt
flask --app app.py run
```

Ensure the appropriate environment variables are set before starting the server to connect to your chosen database.
