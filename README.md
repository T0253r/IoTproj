# System sterowania ogrzewaniem (IoT)

System do zarządzania ogrzewaniem w domu jednorodzinnym, wykorzystujący Raspberry Pi jako centralny serwer oraz mikrokontrolery (Arduino) jako sterowniki.

## Struktura projektu

Projekt składa się z kilku głównych komponentów:

*   **Raspberry Pi (Backend & WebApp):**
    *   `webapp.py` - Aplikacja webowa oparta na Flask, umożliwiająca interakcję użytkownika z systemem.
    *   `heating_manager.py` - Usługa działająca w tle, odpowiedzialna za komunikację MQTT z kontrolerami, odczyt temperatur i sterowanie ogrzewaniem (manualne/automatyczne).
    *   `devices_monitor.py` - Usługa monitorująca podłączone urządzenia w sieci lokalnej i aktualizująca ich status w bazie danych.
    *   `db_init.py` - Skrypt inicjalizujący bazę danych SQLite.

*   **Arduino:**
    *   Kod dla mikrokontrolerów pełniących funkcję sterowników i czujników.

*   **Mock Scripts:**
    *   Skrypty generujące przykładowe dane (kontrolery, urządzenia) do celów testowych i deweloperskich.

## Wymagania

*   Python 3.x
*   Biblioteki wymienione w `requirements.txt`
*   Broker MQTT (np. Mosquitto)

## Instalacja

Zalecane jest użycie środowiska wirtualnego.

1.  Utwórz i aktywuj środowisko wirtualne (opcjonalnie):
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate   # Windows
    ```

2.  Zainstaluj wymagane zależności:
    ```bash
    pip install -r requirements.txt
    ```

## Szybki Start

Aby uruchomić aplikację w trybie deweloperskim z przykładowymi danymi, użyj skryptu `run_webapp.py`. Skrypt ten automatycznie:
1.  Sprawdza zależności.
2.  Inicjalizuje nową bazę danych `iot.db` (usuwając poprzednią).
3.  Tworzy przykładowe kontrolery i urządzenia (mock data).
4.  Weryfikuje zawartość bazy danych.
5.  Uruchamia serwer developerski Flask.

**Uruchomienie:**

```bash
python run_webapp.py
```

Aplikacja będzie dostępna pod adresem: [http://localhost:5000](http://localhost:5000)
Dokumentacja API (jeśli dostępna): [http://localhost:5000/api/docs](http://localhost:5000/api/docs)

## Uruchomienie poszczególnych usług

W środowisku docelowym (np. na Raspberry Pi), usługi powinny działać niezależnie (np. jako serwisy systemd).

*   **Aplikacja Webowa:** `python Raspberry/webapp.py` (lub przez Gunicorn)
*   **Heating Manager:** `python Raspberry/heating_manager.py`
*   **Device Monitor:** `python Raspberry/devices_monitor.py`

Pamiętaj o wcześniejszym zainicjowaniu bazy danych za pomocą `python Raspberry/db_init.py`.