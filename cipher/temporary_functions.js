        /**
         * Wczytuje symulowaną bazę danych z Local Storage, dodaje zaszyfrowany wpis i zapisuje.
         * @param {string} encryptedMessage - Zaszyfrowana wiadomość.
         */
        function saveEncryptedMessage(encryptedMessage) {
            const storageKey = 'simulationOfServerDB';
            let dbArray = [];

            // 1. Wczytaj istniejącą zawartość
            const storedData = localStorage.getItem(storageKey);

            if (storedData) {
                try {
                    dbArray = JSON.parse(storedData);
                    // Upewnij się, że to jest tablica
                    if (!Array.isArray(dbArray)) {
                        console.warn("Dane w Local Storage nie są tablicą. Zostaną zresetowane.");
                        dbArray = [];
                    }
                } catch (e) {
                    console.error("Błąd parsowania Local Storage. Dane zostaną zresetowane.", e);
                    dbArray = [];
                }
            }

            // 2. Dodaj nowy zaszyfrowany wpis
            dbArray.push({
                timestamp: new Date().toISOString(),
                encryptedData: encryptedMessage
            });

            // 3. Zapisz z powrotem do Local Storage
            localStorage.setItem(storageKey, JSON.stringify(dbArray));
            
            const messageEl = document.getElementById('message');
            messageEl.style.backgroundColor = '#d4edda'; // Zielony kolor dla sukcesu
            messageEl.style.color = '#155724';
            messageEl.textContent = `Odpowiedź zaszyfrowana i zapisana do Local Storage (klucz: '${storageKey}').`;
            messageEl.style.display = 'block';

            //console.log("Zapisano zaszyfrowaną wiadomość do Local Storage.", dbArray);
        }



                // TYMCZASOWA FUNKCJA DO ŁADOWANIA DANYCH Z LOCAL-STORAGE
        function LoadEncryptedMessage() {
            const storageKey = 'simulationOfServerDB';
            let dbArray = [];

            // 1. Wczytaj istniejącą zawartość
            const storedData = localStorage.getItem(storageKey);

            if (storedData) {
                try {
                    dbArray = JSON.parse(storedData);
                    // Upewnij się, że to jest tablica
                    if (!Array.isArray(dbArray)) {
                        console.warn("Dane w Local Storage nie są tablicą. Zostaną zresetowane.");
                        dbArray = [];
                    }
                } catch (e) {
                    console.error("Błąd parsowania Local Storage. Dane zostaną zresetowane.", e);
                    dbArray = [];
                }
            }

            return dbArray;
        }

        // TYMCZASOWA FUNKCJA DO CZYSZCZENIA DANYCH Z LOCAL-STORAGE
        function ClearServerSimulation(){
            const storageKey = 'simulationOfServerDB';
            localStorage.removeItem(storageKey);
        }