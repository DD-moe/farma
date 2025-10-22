import aiohttp.web
import sqlite3
import json
import os
from datetime import datetime
import aiohttp_cors # Wymagana nowa biblioteka do CORS

# --- Konfiguracja ---
DB_PATH = 'survey_data.db'
ACCESS_TOKEN = 'BardzoTajnyTokenDostepu123'  # Zmień na bezpieczny, generowany token!
TABLE_NAME = 'surveys'
ALLOWED_ORIGINS = '*' # Zmień na listę dozwolonych subdomen, np. ['https://twoja.subdomena.pl']
# --------------------

# --- Funkcje Bazy Danych ---

def setup_database():
    """Inicjalizuje bazę danych i tabelę. Uruchamiana na starcie aplikacji."""
    if os.path.exists(DB_PATH):
        print(f"Baza danych '{DB_PATH}' już istnieje. Wczytywanie.")
        return

    print(f"Baza danych '{DB_PATH}' nie istnieje. Tworzenie i konfiguracja.")
    try:
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
        print(f"Tabela '{TABLE_NAME}' została utworzona.")
    except sqlite3.Error as e:
        print(f"Błąd konfiguracji bazy danych: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# --- Funkcje Walidacji i Pomocnicze ---

def get_db_conn(request):
    """Pobiera połączenie z bazą danych z obiektu aplikacji."""
    return request.app['db_conn']

def check_auth(request):
    """Sprawdza token dostępu w nagłówku Authorization."""
    # Klient powinien wysłać: Authorization: Bearer <TOKEN>
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        if token == ACCESS_TOKEN:
            return True
    return False

# --- Funkcje Wykonawcze Endpointów ---

async def handle_survey(request):
    """Obsługa POST /survey: Przyjmuje dane i dodaje je do bazy."""
    conn = get_db_conn(request)
    
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return aiohttp.web.json_response(
            {'status': 'error', 'message': 'Nieprawidłowy format JSON'},
            status=400
        )

    message = data.get('message')
    if not message or not isinstance(message, str):
         return aiohttp.web.json_response(
            {'status': 'error', 'message': 'Brak lub nieprawidłowe pole "message"'},
            status=400
        )
    
    current_time_str = datetime.utcnow().isoformat()
    
    try:
        # Wykonanie operacji na bazie danych w puli wątków (domyślny Executor aiohttp)
        cursor = await request.app.loop.run_in_executor(
            None, 
            lambda: conn.cursor().execute(f'INSERT INTO {TABLE_NAME} (data, message) VALUES (?, ?)', 
                                         (current_time_str, message))
        )
        
        await request.app.loop.run_in_executor(None, conn.commit)
        
        print(f"Dodano nowy rekord: {current_time_str}, {message[:20]}...")
        return aiohttp.web.json_response(
            {'status': 'ok', 'message': 'Dane ankiety zapisane pomyślnie', 'lp': cursor.lastrowid},
            status=201
        )
    except sqlite3.Error as e:
        print(f"Błąd SQLite podczas wstawiania: {e}")
        return aiohttp.web.json_response(
            {'status': 'error', 'message': f'Błąd serwera bazy danych: {e}'},
            status=500
        )

async def handle_download(request):
    """Obsługa POST /download: Pobiera wszystkie rekordy i zwraca jako JSON."""
    if not check_auth(request):
        return aiohttp.web.json_response(
            {'status': 'error', 'message': 'Wymagana autoryzacja'},
            status=401
        )
    
    conn = get_db_conn(request)
    
    try:
        def fetch_data():
            cursor = conn.cursor()
            cursor.execute(f'SELECT data, message FROM {TABLE_NAME} ORDER BY lp DESC')
            return cursor.fetchall()
            
        records = await request.app.loop.run_in_executor(None, fetch_data)
        
        data_json = [
            {
                'timestamp': record[0],
                'encryptedData': record[1]
            }
            for record in records
        ]
        
        print(f"Pobrano {len(data_json)} rekordów.")
        return aiohttp.web.json_response(data_json, status=200)
        
    except sqlite3.Error as e:
        print(f"Błąd SQLite podczas pobierania: {e}")
        return aiohttp.web.json_response(
            {'status': 'error', 'message': f'Błąd serwera bazy danych: {e}'},
            status=500
        )

async def handle_clear(request):
    """Obsługa POST /clear: Czyści wszystkie rekordy z tabeli."""
    if not check_auth(request):
        return aiohttp.web.json_response(
            {'status': 'error', 'message': 'Wymagana autoryzacja'},
            status=401
        )
        
    conn = get_db_conn(request)
    
    try:
        def clear_data():
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {TABLE_NAME}')
            deleted_rows = cursor.rowcount
            conn.commit()
            return deleted_rows

        deleted_rows = await request.app.loop.run_in_executor(None, clear_data)
        
        print(f"Usunięto {deleted_rows} rekordów z tabeli.")
        return aiohttp.web.json_response(
            {'status': 'ok', 'message': f'Pomyślnie usunięto {deleted_rows} rekordów'},
            status=200
        )
        
    except sqlite3.Error as e:
        print(f"Błąd SQLite podczas czyszczenia: {e}")
        return aiohttp.web.json_response(
            {'status': 'error', 'message': f'Błąd serwera bazy danych: {e}'},
            status=500
        )

# --- Życiowy Cykl Aplikacji ---

async def on_startup(app):
    """Uruchamiane przy starcie aplikacji: Łączy z bazą danych."""
    # Otwiera jedno, stałe połączenie z bazą danych
    db_conn = sqlite3.connect(DB_PATH)
    # Dodaje połączenie do zasobów aplikacji
    app['db_conn'] = db_conn
    print("Nawiązano stałe połączenie z bazą danych.")

async def on_cleanup(app):
    """Uruchamiane przy zamykaniu aplikacji: Zamyka połączenie z bazą danych."""
    # Zamyka stałe połączenie
    app['db_conn'].close()
    print("Połączenie z bazą danych zostało zamknięte.")

# --- Aplikacja aiohttp i CORS ---

async def init_app():
    """Inicjalizuje aplikację aiohttp, konfiguruje trasy i CORS."""
    app = aiohttp.web.Application()
    
    # Dodanie funkcji cyklu życia (startup/cleanup)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    # Konfiguracja tras POST
    cors = aiohttp_cors.setup(app, defaults={
        # Użycie '*' pozwala na dostęp z dowolnej domeny,
        # dla bezpieczeństwa zmień na konkretną subdomenę/domenę.
        ALLOWED_ORIGINS: aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*", # Niezbędne, by zezwolić na nagłówek Authorization
            allow_methods=["POST", "OPTIONS"],
        )
    })

    # Dodanie tras i konfiguracja CORS
    routes = [
        aiohttp.web.post('/survey', handle_survey),
        aiohttp.web.post('/download', handle_download),
        aiohttp.web.post('/clear', handle_clear),
    ]

    for route in routes:
        app.router.add_route(route.method, route.resource.canonical, route.handler)
        # Dodanie konfiguracji CORS do każdej trasy
        cors.add(route)

    return app

if __name__ == '__main__':
    # Wymagana instalacja: pip install aiohttp_cors
    
    # 1. Konfiguracja bazy danych (synchronicznie, przed startem serwera)
    setup_database()
    
    # 2. Uruchomienie aplikacji aiohttp
    aiohttp.web.run_app(
        init_app(), 
        host='0.0.0.0', 
        port=8080
    )