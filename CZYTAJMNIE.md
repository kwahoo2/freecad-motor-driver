# FreeCAD sterownik silkików krokowych

Celem projektu jest pokazanie jak można sterować silnikami krokowymi bezpośrednio z programu FreeCAD.
Przykład wykorzystuje Raspberry Pi i łatwodostepne sterowniki DRV8825 do zsynchronizowanego sterowania maksymalnie 3 silnikami krokowymi.


## Wymagania

By uruchomić sterować silnikami krokowymi z poziomu programu FreeCAD potrzebne są:

### Sprzęt

* Raspberry PI
* Od 1 do 3 silników krokowych
* Od 1 do 3 sterowników DRV8825
* (Opcjonalnie) inny komputer, jeśli sterowanie ma odbywać się zdalnie

### Oprogramowanie

* biblioteki pigpio zainstalowane na Raspberry Pi
* FreeCAD lub Ondsel ES zainstalowany na Raspberry Pi lub na zdalnym komputerze

## Zawartość repozytorium

Zawartość repozytorium podzielona jest na 3 części, znajdujące się w poniższych katalogach:

* motor-observer - skrypt Pythona, który służy do tworzenia obiektów "MotorObserver" w FreeCAD-zie i monitorowania ich ruchu.
* udp-receiver - program dla Raspberry Pi, który odbiera dane wejściowe z `motor-oberver.py` i steruje silnikami krokowymi
* deltarobot-example - przykład modelu robota delta zbudowanego w zintergrowanym środowisku złożeń programu FreeCAD/Ondsel ES

### Uruchomienie przykładu

* Pobierz zawartość repozytorium:

`git clone https://github.com/kwahoo2/freecad-motor-driver.git`

* Zainstaluj biblioteki pigpio na Raspberry Pi:

`sudo apt install pigpio`

* Skompiluj zawartość katalogu udp-receiver będac na Raspberry Pi:

`make`

* Pobierz [Ondsel ES](https://github.com/Ondsel-Development/FreeCAD/releases) (wersja FreeCAD z zaimplementowanym zunifikowanym środowiskiem złożeń) i uruchom go.
Po uruchomieniu wklej do konsoli Pythona zawartość skryptu `motor-observer.py` a **następnie** otwórz przykład `deltarobot-example.FCStd`
Uwaga: jeśli uruchamiasz FreeCAD na zdalnym komputerze, dostosuj linię `default_remote = '192.168.1.23'` w skrypcie `motor-observer.py`, wpisując tam adress IP Raspberry Pi. Adres możesz też zmienić po starcie skryptu, wpisując w interpreter `adr='192.168.XXX.XXX`.

* Uruchom aplikację sterownika silników na Raspberry Pi (wymaga praw superużytkownika ze względu na dostęp do GPIO):

`sudo ./udp-receiver`

* Porusz złożeniem za pomocą myszy, po uprzednim aktywowaniu go przez podwójne kliknięcie na złożenie `deltabot` w drzewie cech. W widoku raportu Ondsel/FreeCAD powienieneś zobaczyć coś podobnego do:

```
15:53:03  MotorObserver0 [True, 8.391769606205315]
15:53:03  MotorObserver1 [True, 6.743947165727947]
15:53:03  MotorObserver2 [True, 1.9981262137739997]
15:53:03  States changed, sending MotorObservers
```

a w oknie terminala po uruchomieniu `udp-receiver`:

```
Motor 0 enabled: 1, Angle: 8.39177
Motor 1 enabled: 1, Angle: 6.74395
Motor 2 enabled: 1, Angle: 1.99813
```

![Main Window][mw]

[mw]: https://raw.githubusercontent.com/kwahoo2/freecad-motor-driver/main/.github/images/mw_pl.png "Main Window"

## Podłączenie sterowników DRV8825
Pinout dla 3 sterowników jest zdefiniowany w `pigpio_driver.cpp`:

```
static const int enablPin0 = 4; // GPIO 4, physical pin 7
static const int enablPin1 = 20; // GPIO 20, physical pin 38
static const int enablPin2 = 17; // GPIO 17, physical pin 11
static const int dirPin0 = 5; // GPIO 5, physical pin 29
static const int stepPin0 = 6; // GPIO 6, physical pin 31
static const int dirPin1 = 12; // GPIO 12, physical pin 32
static const int stepPin1 = 26; // GPIO 26, physical pin 37
static const int dirPin2 = 27; // GPIO 27, physical pin 13
static const int stepPin2 = 22; // GPIO 22, physical pin 15
```

## Tworzenie nowych obiektów obserwujących

Po utworzeniu nowego dokumentu, możesz utworzyć nowy obiekt MotorObserver wpisując w konsoli FreeCAD:
`create_observer()`

Ustaw go w pozycji docelowej i dowiaż do śledzonej osi, np używając wiązania `Create a Fixed Joint`. Następnie ustaw aktualną pozycję jako pozycję bazową:
`set_base_pl()`

Po obrocie obiektu, powinieneś zobaczyć zmianę atrybutu _Transf Angle_ i w konsoli programu FreeCAD:

```
16:21:19  MotorObserver0 [True, 17.000000000000004]
16:21:19  Dummy1motor added for padding
16:21:19  Dummy2motor added for padding
16:21:19  States changed, sending MotorObservers
```

W podobny sposób możesz dodać dwa kolejne obiekty.

![Single Observer][so]

[so]: https://raw.githubusercontent.com/kwahoo2/freecad-motor-driver/main/.github/images/single_observer.png "Observer"