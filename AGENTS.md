# Utveckling

Använd den befintliga checkouten. Varje molnuppgift har redan en isolerad miljö; skapa ingen Git-worktree om användaren inte uttryckligen ber om det.

## Kommandon

Kör från repots rot. Python 3.10+ och Pygame 2.6.1 krävs.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python main.py --headless --smoke-test
```

Interaktivt spel kräver grafiskt skrivbord: `.venv/bin/python main.py`. Headless-läget använder SDL:s virtuella bild- och ljudenheter och avslutar bara automatiskt tillsammans med `--smoke-test`.

## Struktur och spelkrav

`main.py` hanterar inmatning och huvudloop, `game.py` simuleringen, `levels.py` bandata, `render.py` presentation och `audio.py` ljud. Håll spelreglerna oberoende av ett aktivt fönster så att de går att testa utan skrivbord. Återanvänd `Game`, `InputState` och `teleport_player` i tester.

Bevara svensk speltext och den egenritade grafiken och egenkomponerade ljuden. Undvik externa tillgångar och ytterligare beroenden utan ett konkret behov. Tre banor och tre fiendetyper krävs: vandraren tål varken hopp eller skott, pansarkrypet kan bara skjutas och taggfienden är odödlig. Skjutbonus krävs för att skjuta. Slutbossen har 60 HP; skott gör 4 skada, hopp gör 3. Bossen ska spruta eld och målgången ska vara låst tills den är besegrad.

Verifiera ändrade spelregler med relevanta beteendetester och kör renderingskontrollen efter grafiska ändringar. Skärmbilder och genererade filer ska ligga i `/tmp` eller en ignorerad katalog. Lägg aldrig `.venv` eller cachefiler i Git.
