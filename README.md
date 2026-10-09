# VoltVault

Panel do ewidencji komponentów elektronicznych, przeznaczony m.in. dla Raspberry Pi Zero. Nazwa aplikacji to **VoltVault**. Karta jest rozpoznawana po etykiecie `BACKUP_SD` lub UUID `79A2-FD57`. Karta jest montowana pod `/mnt/VoltVault`; bez niej panel pokazuje ekran oczekiwania, a API nie udostępnia danych magazynu.

## Funkcje

- strona główna (`/`) od razu pokazuje magazyn, gdy karta jest gotowa;
- wyszukiwanie, filtrowanie, dodawanie, edycja i usuwanie elementów;
- liczniki łącznej liczby sztuk, różnych pozycji i pozycji z zapasem do 5 sztuk;
- dane `elements.json` i obrazy są zapisywane na karcie SD;
- wszystkie pliki stylów i JavaScriptu są lokalne — strona nie pobiera zasobów z internetu;
- po wykryciu i zamontowaniu karty następuje 30-sekundowe odliczanie do restartu urządzenia; przycisk pozwala zrestartować je od razu;
- po restarcie, jeśli karta jest zamontowana, aplikacja przechodzi prosto do magazynu.

## Pełny emulator aplikacji na Windows

Do sprawdzenia całego panelu nie potrzebujesz Raspberry Pi, karty SD ani ręcznego kopiowania plików na urządzenie docelowe. Emulator uruchamia ten sam serwer, widoki, API oraz operacje magazynowe. Wirtualna karta jest zwykłym folderem `emulator_sd` w katalogu projektu; restart jest symulowany i nigdy nie restartuje Windowsa.

1. Zainstaluj Python 3.10 lub nowszy z opcją **Add Python to PATH**.
2. Dwukrotnie kliknij `start-emulator.bat`.
3. Przy pierwszym uruchomieniu skrypt instaluje zależności Python (wymaga wtedy internetu). Późniejsze uruchomienia działają lokalnie. Bez internetu skopiuj zgodny folder `wheelhouse` do projektu; skrypt użyje go zamiast sieci.
4. Otwórz `http://127.0.0.1:8000/`.
5. Na ekranie startowym kliknij **Włóż wirtualną kartę SD**. Zobaczysz odliczanie; możesz poczekać na symulowany restart albo kliknąć przycisk natychmiastowego restartu.
6. W panelu możesz dodawać, edytować, usuwać, wyszukiwać i filtrować elementy. Przyciski emulatora pozwalają symulować restart, wyjąć kartę oraz wyczyścić dane testowe.

W emulatorze można przetestować cały przepływ aplikacji: ekran braku karty, włożenie i wyjęcie karty, odliczanie, restart, trwały zapis, listę i statystyki magazynu oraz wszystkie operacje na elementach. Zdjęcia i plik `elements.json` zapisują się w `emulator_sd`; dane zostają po zamknięciu i ponownym uruchomieniu emulatora. **Wyczyść dane testowe** usuwa elementy i obrazy z wirtualnej karty.

Emulator nasłuchuje tylko na `127.0.0.1`, więc nie wystawia trybu symulacji w sieci. Zatrzymasz go przez `Ctrl+C` w oknie konsoli. Folder `.venv` i `emulator_sd` tworzą się lokalnie i nie trzeba ich przenosić na Raspberry Pi.

## Karta SD na Raspberry Pi

Aplikacja rozpoznaje kartę po etykiecie **`BACKUP_SD`** lub UUID **`79A2-FD57`** podanym dla Twojej karty. Nie zmieniaj etykiety ani nie formatuj karty. Punkt montowania aplikacji to `/mnt/VoltVault`.

Sprawdź, czy system widzi kartę i potwierdź jej UUID oraz system plików exFAT:

```sh
lsblk -f
sudo blkid /dev/sda1
```

Dodaj do `/etc/fstab` wpis używający UUID (zastąp go tylko wtedy, gdy `blkid` pokazuje inny UUID):

```fstab
UUID=79A2-FD57  /mnt/VoltVault  exfat  defaults,nofail,x-systemd.device-timeout=5s  0  0
```

Alternatywnie zamiast `UUID=79A2-FD57` możesz użyć `LABEL=BACKUP_SD`. Utwórz punkt montowania i sprawdź konfigurację:

```sh
sudo mkdir -p /mnt/VoltVault
sudo mount /mnt/VoltVault
findmnt /mnt/VoltVault
```

Jeżeli system zgłosi brak obsługi exFAT, doinstaluj obsługę exFAT dla Raspberry Pi OS, a następnie ponów montowanie.

Aplikacja próbuje zamontować `/mnt/VoltVault` po wykryciu karty. Konto usługi potrzebuje ograniczonego uprawnienia sudo do montowania tej jednej ścieżki i restartu urządzenia. Otwórz konfigurację sudoers:

```sh
sudo visudo -f /etc/sudoers.d/voltvault
```

Dodaj wpis; zamień `ndn02` na konto uruchamiające usługę i dopasuj ścieżkę `mount` do wyniku `command -v mount`:

```sudoers
ndn02 ALL=(root) NOPASSWD: /usr/bin/mount /mnt/VoltVault, /sbin/reboot, /usr/sbin/reboot
```

Sprawdź montowanie bez restartowania urządzenia:

```sh
sudo -n /usr/bin/mount /mnt/VoltVault
```

## Instalacja aplikacji

Wymagania: Python 3.10+ i jednorazowo zainstalowane zależności z `requirements.txt`.

Na Raspberry Pi OS / Linux:

```sh
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
cd /ścieżka/do/VoltVault
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jeśli docelowe urządzenie nie ma internetu, przygotuj pliki wheel na urządzeniu z dostępem do sieci dla tej samej architektury i wersji Pythona, a następnie skopiuj folder `wheelhouse/` na Raspberry Pi:

```sh
python -m pip download -r requirements.txt -d wheelhouse
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

### Uruchamianie automatyczne po restarcie Raspberry Pi

W projekcie jest jednostka systemd `deploy/voltvault.service`. Skopiuj projekt do `/home/ndn02/VoltVault` albo zmień w pliku `User`, `Group` i `WorkingDirectory` na właściwe konto i lokalizację. Następnie:

```sh
sudo cp deploy/voltvault.service /etc/systemd/system/voltvault.service
sudo systemctl daemon-reload
sudo systemctl enable --now voltvault.service
sudo systemctl status voltvault.service
```

Ta usługa uruchomi panel automatycznie po restarcie urządzenia. Konto usługi musi odpowiadać kontu podanemu w pliku sudoers wyżej.

Do ręcznego uruchomienia na czas konfiguracji:

```sh
./start.sh
```

Na Windowsie do zwykłego trybu bez emulatora (bez wirtualnej karty):

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Otwórz panel przez IP

Gdy usługa działa, z urządzenia w tej samej sieci otwórz `http://ADRES-IP-RASPBERRY-PI:8000/`. Port 8000 musi być dozwolony w zaporze. Przykład: `http://192.168.1.50:8000/`.

## Zachowanie przy braku karty

Aplikacja sprawdza kartę co 2 sekundy. Gdy jej brakuje, wyświetla instrukcję włożenia karty. Jeśli system widzi etykietę, ale nie może zamontować karty, ekran pokaże błąd montowania. Po zamontowaniu rozpoczyna się 30-sekundowe odliczanie i restart hosta; przycisk uruchamia restart natychmiast. Po ponownym uruchomieniu panel czyta dane z karty. Jeśli brak uprawnień do restartu, błąd będzie widoczny na ekranie.

Dane znajdują się na karcie w `/mnt/VoltVault/elements.json` oraz `/mnt/VoltVault/images/`. Przed wyjęciem karty zatrzymaj aplikację i bezpiecznie ją odmontuj.
