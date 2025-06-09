# Bielik with da Pepper

Konrad chcial Bielik with da Pepper, to robimy Bielik with da Pepper. Sprobujemy zeby Pepper gadal glosem z Bielika. Pepper nasluchuje audio, jak cos ktos powiedzial to przekazujemy tekst do Bielika, Bielik nam odpowiada i wysylamy to do Peppera.

---

## Spis Tresci

- [Dzialanie_programu] (#Dzialanie_programu)
- [Uzywane_moduly_AL] (#uzywane-moduly-AL)
- [Struktura_Projektu] (#struktura-projektu)
- [Opisy_plikow] (#opisy-plikow)
- [Autorzy_i_kontakt] (#autorzy_i_kontakt)
  
---

## Dzialanie_programu

- Zbieranie audio z Peppera
- Przesylanie audio do XXX i speech2text
- Przeslanie do Bielika tekstu
- Bielik nam zwraca glos
- Wysylamy do Peppera

---

## Uzywane moduly AL

- AL


## Struktura projektu

```
Bielik_with_pepper
├── audio_soundprocessing.py # Tu chcemy rzezbic
|
├── SoundReciver.py         # Mozliwie ze do wywalenia, ale chwilowo nie tykamy
|
├── requirements.txt
|
└── main.py
```

## Opisy plikow

- **audio_soundprocessing.py**: Tutaj zamierzamy zamiescic glowna logike programu, zbieranie audio i przesylanie
- **SoundReciver.py**: Deprecated, ale dzialal, niech zostanie chwilowo chlopak
- **main.py**: Nie zgadniesz co robi
