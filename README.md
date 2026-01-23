## Co robi kod i jak ma być odpalany
 - db_init.py - inicjalizacja bazy danych, odpalany ręcznie
 - heating_manager.py - komunikuje się ze kontrolerami po mqtt, czyta z bazy potrzebne dane (temperatury zadane przez użytkowników, dane o temperaturach aktualnych  i automatycznych oraz dane o podłączonych urządzeniach), jest odpowiedzialny za ustawianie zadanych temperatur na sterownikach (manulanych i automatycznych), działa jako system service
 - devices_monitor.py - aktualizacja informacji o podłączonych urządzeniach w bazie danych, działa jako system service
 - web_server.py - serwer webowy na którym użytkownicy mogą sobie klikać i ogólnie wchodzić w interakcję, pisze po bazie danych, nie komunikuje się po mqtt, trzeba użyć gunicorn (albo czegoś innego) do odpalenia tego jako system service

 ### Robimy jeden requirements.txt i nie robimy venvów na malinie
 Ostatnio wyszły z tego problemy, a jak tamten kod ma działać jako system service to lepiej wszystkie dependency zainstalować ogólnosystemowo

 ### Lokacja bazy danych
 Dalej nie wiem czy lepiej jest aby to była jakaś względna czy bezwzględna ścieżka, ale na razie wydaje mi się że lepiej to zrobić bezwzględnie (łatwiej usługi systemowe skonfigurować)
 Aktualna ścieżka bazy: **/home/akkm/iot.db**

 ### Kanały mqtt
  - controllers/x/target-temp -> malina publikuje zadane temperatury dla sterownika z ID = x
  - controllers/x/curr-temp -> sterownik z ID = x publikuje odczytaną temperaturę
Te dwa tematy per sterownik wystarczą, bo i tak są wysyłane regularne update'y, które działają jako heartbeat