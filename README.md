## Co robi kod i jak ma być odpalany
 - db_init.py - inicjalizacja bazy danych, odpalany ręcznie
 - mqtt_controller.py - komunikuje się ze sterownikami po mqtt, czyta z bazy potrzebne dane (temperatury zadane przez użytkowników, dane o temperaturach aktualnych  i automatycznych oraz dane o podłączonych urządzeniach), jest odpowiedzialny za ustawianie zadanych temperatur na sterownikach (manulanych i automatycznych), działa jako system service
 - devices_monitor.py - aktualizacja informacji o podłączonych urządzeniach w bazie danych, działa jako system service
 - web_server.py - serwer webowy na którym użytkownicy mogą sobie klikać i ogólnie wchodzić w interakcję, pisze po bazie danych, nie komunikuje się po mqtt, trzeba użyć gunicorn (albo czegoś innego) do odpalenia tego jako system service

 ### Robimy jeden requirements.txt i nie robimy venvów na malinie
 Ostatnio wyszły z tego problemy, a jak tamten kod ma działać jako system service to lepiej wszystkie dependency zainstalować ogólnosystemowo