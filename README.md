# Glödsprång: Jakten på askkronan

Ett komplett 2D-plattformsspel i Python och Pygame, inspirerat av klassiska plattformsäventyr. Ta dig från Vindängarna genom Bärnstensklyftan till Glödens fäste och besegra den eldsprutande Askkungen.

Spelets grafik, musik och ljudeffekter skapas i kod. Inga externa bildfiler, ljudfiler, konton eller API-nycklar behövs.

## Installera och spela

Du behöver **Python 3.10 eller senare** och en dator med grafisk skrivbordsmiljö. Det enda Python-beroendet är **Pygame 2.6.1**.

Linux/macOS, från repots rot:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows, i PowerShell från repots rot:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Om PowerShell blockerar aktiveringsskriptet kan du köra miljöns Python direkt:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Spelfönstret kan storleksändras. Bilden behåller sina proportioner och spelets fysik körs med ett fast tidssteg.

## Kontroller

| Tangent | Funktion |
| --- | --- |
| A/D eller vänster/höger pil | Gå |
| Mellanslag, W eller uppåtpil | Hoppa; håll inne för ett högre hopp |
| X eller J | Skjut efter att du har hämtat en skjutbonus; håll inne för upprepade skott |
| P eller Esc | Pausa eller fortsätt |
| M | Slå av/på musik och ljudeffekter |
| R | Börja om aktuell bana eller bossens kontrollpunkt med tre liv |
| Enter | Starta, fortsätt från paus eller försök igen |

Menyerna kan också styras med musen. Esc avslutar från huvudmenyn.

## Så fungerar äventyret

De tre handbyggda banorna har hinder, avsatser, hål och mynt att samla. Den blå glödbonusen ger **skjutbonus**. Du måste hämta den innan du kan skjuta; bonusen följer med till nästa bana.

| Fiende | Så hanterar du den |
| --- | --- |
| Vandraren | Hoppa på den ovanifrån eller skjut den. |
| Pansarkrypet | Kan bara besegras med skott; hopp skadar dig. |
| Taggfienden | Är odödlig och måste hoppas över. |

Du börjar med tre liv. Fiendekontakt och eld kostar ett liv och ger en kort stunds osårbarhet. Om du faller i ett hål förlorar du ett liv och börjar om banan från dess start eller den aktiverade kontrollpunkten. En ny bana fyller på till tre liv. R ger alltid möjlighet att försöka igen.

I slutet av bana tre väntar **Askkungen**, en bepansrad, eldsprutande boss. Han besegras av **15 träffande skott eller 20 hopp på huvudet**. Du kan även kombinera angreppen: bossen har 60 hälsopoäng, skott gör 4 skada och hopp gör 3. Elden kommer i salvor och blir tätare när bossen är försvagad. Avsatserna i arenan hjälper dig att nå hans huvud. En kontrollpunkt strax före bossen ger dig skjutbonus vid omstart. När bossen faller kan du passera den sista målporten.

## Ljud

Bakgrundsmusiken är en egenkomponerad, loopande chiptune. Hopp, skott, bonusar, skada, fiender, eld och seger har egna syntetiserade ljudeffekter. Spelet kan även köras när en ljudenhet saknas.

Starta utan ljud med:

```bash
python main.py --mute
```

## Tester och molnmiljö

Från repots rot på Linux/macOS:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python main.py --headless --smoke-test
```

Det första kommandot kör spelreglernas tester. Det andra startar Pygame med virtuella bild- och ljudenheter, simulerar och ritar de tre banorna, bossen och menyerna och avslutar automatiskt. Det går att spara den sista spelrutan:

```bash
.venv/bin/python main.py --headless --smoke-test --screenshot /tmp/glodsprang.png
```

På Windows använder du `.venv\Scripts\python.exe` i stället för `.venv/bin/python` och väljer en lokal sökväg för skärmbilden.

En molnmiljö utan grafiskt skrivbord lämpar sig för utveckling och dessa automatiska kontroller. För att spela med tangentbord, synlig bild och hörbart ljud kör du `python main.py` på en dator med bildskärm. Headless-läget visar inget fönster.

## Projektets delar

| Fil | Ansvar |
| --- | --- |
| `main.py` | Startargument, fönster, inmatning och huvudloop |
| `game.py` | Spelregler, fysik, kollisioner, fiender och boss |
| `levels.py` | De tre banornas geometri, föremål och fiender |
| `render.py` | Grafik, animationer, bakgrunder och menyer |
| `audio.py` | Syntes av musik och ljudeffekter |
| `tests/` | Automatiska tester av spelets beteende |
