# Bielik with da Pepper

Konrad chcial Bielik with da Pepper, to robimy Bielik with da Pepper. Sprobujemy zeby Pepper gadal glosem z Bielika. Pepper nasluchuje audio, jak cos ktos powiedzial to przekazujemy tekst do Bielika, Bielik nam odpowiada i wysylamy to do Peppera.

---

## Spis Treści

- [Bielik with da Pepper](#bielik-with-da-pepper)
  - [Spis Treści](#spis-treści)
  - [Struktura projektu](#struktura-projektu)
  - [Opis plików i katalogów](#opis-plików-i-katalogów)
  - [Używane moduły AL](#używane-moduły-al)
  
---

## Struktura projektu

```bash
.
├── camera.py
├── images
│   ├── bottle1.jpg
│   ├── cola1.jpg
│   └── cola2.jpg
├── LLM_and_saying.py
├── main_Nao_debata.py
├── main_Pepper_debata.py
├── main.py
├── metal_bottle_detector.py
├── motion.py
├── prompts
│   ├── Narwicki.prompt
│   ├── system_message.prompt
│   └── Tarnowski.prompt
├── README.md
├── requirements.txt
├── robot_action_logic.py
├── robot_auth.py
├── SoundReciver.py
└── yolov8n.pt
```

## Opis plików i katalogów

- **`main.py`**: Główny plik uruchomieniowy projektu.
- **`main_Nao_debata.py`**: Główny plik do debaty z użyciem robota Nao.
- **`main_Pepper_debata.py`**: Główny plik do debaty z użyciem robota Pepper.
- **`camera.py`**: Moduł do obsługi kamery robota, robienia zdjęć i oznaczania na nich kątów.
- **`LLM_and_saying.py`**: Obsługuje interakcję z modelem językowym (LLM) oraz syntezę mowy robota.
- **`metal_bottle_detector.py`**: Skrypt do detekcji metalowych butelek, prawdopodobnie z użyciem modelu `yolov8n.pt`.
- **`motion.py`**: Odpowiada za sterowanie ruchem robota.
- **`robot_action_logic.py`**: Zawiera logikę akcji wykonywanych przez robota.
- **`robot_auth.py`**: Moduł do autentykacji i połączenia z robotem.
- **`SoundReciver.py`**: Odbiera dźwięk z mikrofonów robota. (Możliwie, że przestarzały).
- **`requirements.txt`**: Lista zależności Pythona wymaganych do uruchomienia projektu.
- **`yolov8n.pt`**: Wytrenowany model sieci neuronowej YOLOv8, używany do detekcji obiektów.
- **`images/`**: Katalog zawierający przykładowe obrazy.
- **`prompts/`**: Katalog z plikami zawierającymi prompty dla modelu językowego.

---

## Używane moduły AL

- `ALVideoDevice`
- `ALTextToSpeech`
- `ALAudioDevice`
- `ALMotion`
