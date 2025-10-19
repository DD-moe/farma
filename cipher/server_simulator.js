// server_simulator.js

// Stały token dostępu dla roli "analitic"
const ACCESS_TOKEN = "super_tajny_token_123";

// Symulowana baza danych (tablica w pamięci)
let database = [];
let nextLp = 1; // Liczba porządkowa

// Tablica do przechowywania portów komunikacyjnych (połączeń z klientami)
const ports = [];

// Funkcja obsługująca nowe połączenia z klientami
self.onconnect = function(e) {
    const port = e.ports[0];
    ports.push(port); // Dodajemy port do tablicy

    port.onmessage = function(event) {
        const { action, role, token, message } = event.data;
        let response = { success: false, action };

        switch (action) {
            case 'add_entry':
                response = handleAddEntry(role, message, action);
                break;
            case 'read_all':
                response = handleReadAll(role, token, action);
                break;
            case 'read_and_clear':
                response = handleReadAndClear(role, token, action);
                break;
            default:
                response.error = 'Nieznana akcja.';
        }

        // Wysyłamy odpowiedź tylko do klienta, który wysłał żądanie
        port.postMessage(response);
    };

    // Obsługa zamknięcia połączenia (opcjonalnie)
    port.onclose = function() {
        const index = ports.indexOf(port);
        if (index > -1) {
            ports.splice(index, 1);
        }
    };
};

// Funkcja obsługująca dodanie wpisu (rola: "survey")
function handleAddEntry(role, message, action) {
    if (role !== "survey") {
        return { success: false, error: "Brak uprawnień. Wymagana rola: 'survey'." };
    }

    if (!message || typeof message !== 'string' || message.trim() === '') {
        return { success: false, error: "Wiadomość nie może być pusta." };
    }

    const newEntry = {
        lp: nextLp++,
        date: new Date().toISOString(),
        message: message.trim()
    };

    database.push(newEntry);
    console.log(`[Shared Worker] Dodano wpis: LP ${newEntry.lp}`);

    return { success: true, message: `Wpis dodany (LP: ${newEntry.lp}).`, record: newEntry, action: action };
}

// Funkcja obsługująca odczyt wszystkich wpisów (rola: "analitic")
function handleReadAll(role, token, action) {
    if (role !== "analitic" || token !== ACCESS_TOKEN) {
        return { success: false, error: "Brak uprawnień. Wymagana rola: 'analitic' i poprawny token." };
    }

    // Zwracamy kopię bazy danych
    const data = JSON.parse(JSON.stringify(database));
    console.log(`[Shared Worker] Odczytano ${data.length} wpisów.`);

    return { success: true, data: data, message: `Odczytano ${data.length} wpisów.`, action: action };
}

// Funkcja obsługująca odczyt i wyczyszczenie bazy (rola: "analitic")
function handleReadAndClear(role, token, action) {
    if (role !== "analitic" || token !== ACCESS_TOKEN) {
        return { success: false, error: "Brak uprawnień. Wymagana rola: 'analitic' i poprawny token." };
    }

    // 1. Odczyt (kopiowanie danych)
    const dataToReturn = JSON.parse(JSON.stringify(database));

    // 2. Czyszczenie
    const clearedCount = database.length;
    database = [];
    nextLp = 1; // Resetujemy licznik LP

    console.log(`[Shared Worker] Odczytano i wyczyszczono ${clearedCount} wpisów.`);

    return { success: true, data: dataToReturn, message: `Odczytano ${clearedCount} wpisów i wyczyszczono bazę danych.`, action: action };
}