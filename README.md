# VoltVault

Panel do ewidencji elementów elektronicznych dla Raspberry Pi Zero. Karta jest wykrywana po etykiecie `BACKUP_SD` lub UUID `79A2-FD57` i montowana pod `/mnt/VoltVault`. Bez dostępnej karty aplikacja pokazuje ekran oczekiwania, a dane magazynu pozostają niedostępne.

## Funkcje

- magazyn bezpośrednio pod adresem `/`;
- wyszukiwanie i filtrowanie, dodawanie, edycja oraz usuwanie elementów;
- liczniki sztuk, różnych pozycji i zapasów wynoszących 5 sztuk lub mniej;
- zapis elementów i obrazów na wymaganej karcie SD;
- panel stanu: CPU, RAM, zajęte/wolne miejsce na karcie i dysku systemowym oraz transfer sieciowy;
- lokalne zasoby strony — bez pobierania CSS, fontów ani bibliotek z internetu;
- pełny emulator Windows z wirtualną kartą i symulacją restartu.

Statystyki odświeżają się co 5 sekund. Liczniki wysłanych i pobranych MB są sumą liczników aktywnych interfejsów sieciowych od uruchomienia systemu. W emulatorze miejsce wirtualnej karty jest częścią dysku, na którym leży folder `emulator_sd`.

## Emulator aplikacji na Windows

Do sprawdzenia aplikacji nie potrzebujesz Raspberry Pi ani fizycznej karty. Emulator uruchamia ten sam serwer, widoki, API i obsługę magazynu. Restart jest symulowany — Windows nie zostanie zrestartowany.

1. Zainstaluj Python 3.10 lub nowszy i zaznacz **Add Python to PATH**.
2. Uruchom `start-emulator.bat`.
3. Przy pierwszym uruchomieniu skrypt instaluje zależności Python. W tym przypadku wymagane jest połączenie z internetem. Jeśli ma działać bez internetu, umieść zgodny z wersją Pythona i Windowsa katalog `wheelhouse` w folderze projektu — skrypt zainstaluje z niego zależności.
4. Otwórz `http://127.0.0.1:8000/` i kliknij **Włóż wirtualną kartę SD**.
5. Testuj odliczanie, natychmiastowy/symulowany restart, magazyn, edycję, wyszukiwanie i statystyki. W panelu emulatora można też wyjąć kartę lub wyczyścić dane testowe.

Elementy i obrazy emulatora zapisują się w lokalnym folderze `emulator_sd` i pozostają po zamknięciu programu. Przycisk **Wyczyść dane testowe** usuwa elementy i obrazy z tej wirtualnej karty. Zatrzymaj emulator przez `Ctrl+C` w jego oknie. Emulator nasłuchuje wyłącznie na `127.0.0.1`.

## Konfiguracja karty SD na Raspberry Pi

Nie zmieniaj etykiety ani nie formatuj karty. Podane identyfikatory to `BACKUP_SD` i `79A2-FD57`, system plików to exFAT. Najpierw sprawdź urządzenie:

```sh
lsblk -f
sudo blkid /dev/sda1
```

Dodaj wpis do `/etc/fstab` (użyj UUID z wyniku `blkid`; możesz zamiast niego wpisać `LABEL=BACKUP_SD`):

```fstab
UUID=79A2-FD57  /mnt/VoltVault  exfat  defaults,nofail,x-systemd.device-timeout=5s  0  0
```

Utwórz punkt montowania i sprawdź wpis:

```sh
sudo mkdir -p /mnt/VoltVault
sudo mount /mnt/VoltVault
findmnt /mnt/VoltVault
```

Jeśli system zgłosi brak obsługi exFAT, doinstaluj obsługę exFAT dla Raspberry Pi OS.

Aplikacja próbuje zamontować `/mnt/VoltVault` po wykryciu karty. Konto uruchamiające aplikację potrzebuje ograniczonego uprawnienia do tego montowania i restartu urządzenia:

```sh
sudo visudo -f /etc/sudoers.d/voltvault
```

Dodaj wpis, zmieniając `ndn02` na właściwe konto. Sprawdź ścieżki poleceniami `command -v mount` i `command -v reboot` i w razie potrzeby popraw je poniżej:

```sudoers
ndn02 ALL=(root) NOPASSWD: /usr/bin/mount /mnt/VoltVault, /sbin/reboot, /usr/sbin/reboot
```

## Instalacja i uruchamianie na Raspberry Pi OS

Wymagany Python 3.10 lub nowszy. W folderze projektu wykonaj:

```sh
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Gdy Raspberry Pi nie ma internetu, przygotuj paczki wheel dla tej samej architektury i wersji Pythona, skopiuj `wheelhouse/` do projektu, a następnie użyj:

```sh
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

### Automatyczny start systemd

Jednostka systemd znajduje się w `deploy/voltvault.service`. Domyślnie zakłada, że projekt leży w `/home/ndn02/VoltVault` i działa z konta `ndn02`; dostosuj te wartości, jeśli używasz innej ścieżki lub konta.

```sh
sudo cp deploy/voltvault.service /etc/systemd/system/voltvault.service
sudo systemctl daemon-reload
sudo systemctl enable --now voltvault.service
sudo systemctl status voltvault.service
```

Ręczne uruchomienie na czas konfiguracji:

```sh
./start.sh
```

## Wejście przez sieć lokalną

Z urządzenia w tej samej sieci otwórz `http://ADRES-IP-RASPBERRY-PI:8080/`, np. `http://192.168.1.50:8080/`. Port 8080 musi być dozwolony w zaporze.

Dane znajdują się na karcie w `/mnt/VoltVault/elements.json` oraz `/mnt/VoltVault/images/`. Przed wyjęciem karty zatrzymaj aplikację i bezpiecznie ją odmontuj.
