# multimodal-llm-robot-control (starter)

Minimalny starter do testów: **zdjęcie → percepcja → komenda** przy użyciu lokalnego serwera **Ollama**.

## 1) Wymagania

- Windows 10/11
- Python 3.10+ (polecane 3.11)
- Zainstalowane **Ollama** i uruchomiony serwis lokalny

## 1a) Instalacja Ollama (Windows)

Masz dwie proste opcje:

### Opcja A: instalator

1. Pobierz i uruchom instalator z: https://ollama.com/download
2. Po instalacji otwórz nowy terminal.

### Opcja B: winget

```powershell
winget install Ollama.Ollama
```

### Weryfikacja, że Ollama działa

```powershell
ollama --version
ollama list
```

Jeśli API nie odpowiada, uruchom serwer ręcznie:

```powershell
ollama serve
```

Szybki test HTTP (powinno zwrócić JSON):

```powershell
curl http://localhost:11434/api/tags
```

## 2) Instalacja

```powershell
cd e:\AGH\AiR\AiR_mgr\multimodal-llm-robot-control
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### 2a) CLI i workflow (ważne na Windows)

- Po `pip install -e .` komenda `ollama-demo` jest instalowana do `.venv\Scripts`.
- Jeśli masz aktywne venv (`.\.venv\Scripts\Activate.ps1`), możesz używać:

```powershell
ollama-demo --help
```

- Jeśli nie masz aktywnego venv (albo PATH nie widzi `.venv\Scripts`), uruchom pełną ścieżką:

```powershell
.\.venv\Scripts\ollama-demo.exe --help
```

- Gdy zmienisz `pyproject.toml` (np. zależności lub `[project.scripts]`), wykonaj ponownie:

```powershell
pip install -e .
```

## 3) Model w Ollama

1. Uruchom Ollama.
2. Pobierz model:

```powershell
ollama pull gemma3
ollama list
```

Uwaga: **nie każdy wariant Gemma jest multimodalny**. Jeśli model nie obsługuje obrazów, demo nadal zadziała, ale analiza zdjęcia będzie słaba lub zakończy się błędem. Wtedy przetestuj model VLM dostępny w Ollama (np. `llava`) albo wariant Gemma wspierający obrazy (jeśli masz taki w Ollama).

## 4) Uruchomienie demo

### Test ze zdjęciem

```powershell
ollama-demo --image "C:\path\to\photo.jpg" --model gemma3 --task "Określ położenie robota i zaproponuj bezpieczną komendę."

# albo:
python -m ollama_demo.cli --image "C:\path\to\photo.jpg" --model gemma3 --task "Określ położenie robota i zaproponuj bezpieczną komendę."
```

### ESP32-CAM (snapshot po HTTP)

Jeśli ESP32-CAM wystawia endpoint ze zdjęciem (często to `/capture`, czasem `/jpg` lub podobny),
możesz testować bez ręcznego zapisywania pliku:

```powershell
ollama-demo --snapshot-url "http://192.168.1.123/capture" --model gemma3 --task "Oceń czy jechać prosto czy stop."

# albo:
python -m ollama_demo.cli --snapshot-url "http://192.168.1.123/capture" --model gemma3 --task "Oceń czy jechać prosto czy stop."
```

Jeśli snapshot ładuje się wolno, zwiększ timeout:

```powershell
ollama-demo --snapshot-url "http://192.168.1.123/capture" --snapshot-timeout 30 --model gemma3

# albo:
python -m ollama_demo.cli --snapshot-url "http://192.168.1.123/capture" --snapshot-timeout 30 --model gemma3
```

### Zapis wyniku do pliku

```powershell
ollama-demo --image "C:\path\to\photo.jpg" --model gemma3 --out outputs\result.json --raw-out outputs\raw.json

# albo:
python -m ollama_demo.cli --image "C:\path\to\photo.jpg" --model gemma3 --out outputs\result.json --raw-out outputs\raw.json
```

## 5) Co zwraca model

Program oczekuje odpowiedzi w JSON (walidowanej przez Pydantic):

- `robot.visible` i opcjonalnie `robot.bbox` (piksele)
- `command.*` (action + prędkości)
- `confidence` 0..1

## 6) Następny krok (integracja z robotem)

Na start to tylko "percepcja + propozycja komendy". Gdy będziesz gotowy:
- ustalimy format komend pod Twojego robota (np. ROS2 `geometry_msgs/Twist`),
- dodamy node publikujący komendy i/lub pobierający obraz z kamery.


Invoke-WebRequest "http://192.168.10.227/jpg" -OutFile ".\outputs\snapshot.jpg"                                              

ollama-demo --image ".\outputs\snapshot.jpg" --model llava:latest --out ".\outputs\parsed.json" --raw-out ".\outputs\raw.json"

