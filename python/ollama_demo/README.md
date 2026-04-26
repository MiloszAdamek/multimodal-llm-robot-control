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
python -m ollama_demo.cli --image "C:\path\to\photo.jpg" --model gemma3 --task "Określ położenie robota i zaproponuj bezpieczną komendę."

### ESP32-CAM (snapshot po HTTP)

Jeśli ESP32-CAM wystawia endpoint ze zdjęciem (często to `/capture`, czasem `/jpg` lub podobny),
możesz testować bez ręcznego zapisywania pliku:

```powershell
python -m ollama_demo.cli --snapshot-url "http://192.168.1.123/capture" --model gemma3 --task "Oceń czy jechać prosto czy stop."
```

Jeśli snapshot ładuje się wolno, zwiększ timeout:

```powershell
python -m ollama_demo.cli --snapshot-url "http://192.168.1.123/capture" --snapshot-timeout 30 --model gemma3
```
```

### Zapis wyniku do pliku

```powershell
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
