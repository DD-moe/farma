import aiohttp.web
import sqlite3
import json
import os
from datetime import datetime
import aiohttp_cors

DB_PATH = 'survey_data.db'
ACCESS_TOKEN = 'BardzoTajnyTokenDostepu123'
TABLE_NAME = 'surveys'


def setup_database():
    if not os.path.exists(DB_PATH):
        print(f"Tworzenie nowej bazy danych: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                lp INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("Baza danych utworzona.")
    else:
        print("Baza danych istnieje.")


def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        return token == ACCESS_TOKEN
    return False


async def handle_survey(request):
    """POST /survey — zapisuje dane tekstowe do bazy"""
    message = await request.text()
    if not message:
        return aiohttp.web.json_response({'status': 'error', 'message': 'Brak danych'}, status=400)

    current_time_str = datetime.utcnow().isoformat()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'INSERT INTO {TABLE_NAME} (data, message) VALUES (?, ?)',
                       (current_time_str, message))
        conn.commit()
        lp = cursor.lastrowid
        conn.close()

        print(f"Dodano rekord {lp}: {message[:10]}...")
        return aiohttp.web.json_response({'status': 'ok', 'lp': lp}, status=201)
    except sqlite3.Error as e:
        print(f"Błąd SQLite: {e}")
        return aiohttp.web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def handle_download(request):
    """POST /download — zwraca wszystkie rekordy"""
    if not check_auth(request):
        return aiohttp.web.json_response({'status': 'error', 'message': 'Brak autoryzacji'}, status=401)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'SELECT data, message FROM {TABLE_NAME} ORDER BY lp DESC')
        records = cursor.fetchall()
        conn.close()

        data_json = [{'timestamp': r[0], 'encryptedData': r[1]} for r in records]
        print(f"Pobrano {len(data_json)} rekordów.")
        return aiohttp.web.json_response(data_json, status=200)
    except sqlite3.Error as e:
        print(f"Błąd SQLite: {e}")
        return aiohttp.web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def handle_clear(request):
    """POST /clear — usuwa wszystkie rekordy"""
    if not check_auth(request):
        return aiohttp.web.json_response({'status': 'error', 'message': 'Brak autoryzacji'}, status=401)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {TABLE_NAME}')
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"Usunięto {deleted_rows} rekordów.")
        return aiohttp.web.json_response({'status': 'ok', 'deleted': deleted_rows}, status=200)
    except sqlite3.Error as e:
        print(f"Błąd SQLite: {e}")
        return aiohttp.web.json_response({'status': 'error', 'message': str(e)}, status=500)


def handler(request):
    return aiohttp.web.Response(text="Hello!", headers={"X-Custom-Server-Header": "Custom data"})


async def init_app():
    app = aiohttp.web.Application()
    cors = aiohttp_cors.setup(app)

    # Prosty GET /
    cors.add(
        app.router.add_route("GET", "/", handler),
        {"*": aiohttp_cors.ResourceOptions(allow_credentials=True)}
    )

    resource_survey = app.router.add_resource('/survey')
    cors.add(
        resource_survey.add_route('POST', handle_survey), {
            "https://farma.1ioe.top": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=("X-Custom-Server-Header",),
                allow_headers=("X-Requested-With", "Content-Type", "Authorization"),
                allow_methods=("POST", "OPTIONS"),
                max_age=3600,
            )
        })

    resource_download = app.router.add_resource('/download')
    cors.add(
        resource_download.add_route('POST', handle_download), {
            "https://farma.1ioe.top": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=("X-Custom-Server-Header",),
                allow_headers=("X-Requested-With", "Content-Type", "Authorization"),
                allow_methods=("POST", "OPTIONS"),
                max_age=3600,
            )
        })

    resource_clear = app.router.add_resource('/clear')
    cors.add(
        resource_clear.add_route('POST', handle_clear), {
            "https://farma.1ioe.top": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers=("X-Custom-Server-Header",),
                allow_headers=("X-Requested-With", "Content-Type", "Authorization"),
                allow_methods=("POST", "OPTIONS"),
                max_age=3600,
            )
        })
       

    return app


if __name__ == "__main__":
    setup_database()
    aiohttp.web.run_app(init_app(), port=21435)
