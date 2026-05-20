# app_zmieniony.py
# Wersja z dwuetapowym flow:
# 1) pobranie danych ze Stravy
# 2) analiza Gemini uruchamiana on demand

import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
from PIL import Image
import re
import json

st.set_page_config(
    page_title="Asystent treningowy AI",
    page_icon="🏃",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600&display=swap');

    .stApp { background-color: #0f0f0f; color: #ffffff; }
    header[data-testid="stHeader"] { background-color: #0f0f0f !important; border-bottom: 1px solid #FC4C02; }
    #MainMenu, footer, header .stDeployButton { visibility: hidden; }

    h1, h2, h3, h4 {
        font-family: 'Share Tech Mono', monospace !important;
        color: #FC4C02 !important;
    }
    p, li, span, label, .stMarkdown {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 16px !important;
        color: #ffffff !important;
    }

    .stSidebar { background-color: #1a1a1a; }
    .stSidebar p, .stSidebar label, .stSidebar .stMarkdown {
        color: #ffffff !important;
        font-family: 'Rajdhani', sans-serif !important;
    }
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {
        color: #FC4C02 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }

    .stButton > button {
        background-color: #FC4C02;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-family: 'Share Tech Mono', monospace !important;
        width: 100%;
        padding: 12px;
    }
    .stButton > button:hover { background-color: #e04400; }

    .stDownloadButton > button {
        background-color: #FC4C02 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: bold !important;
        padding: 12px !important;
    }

    .metric-card {
        background-color: #1a1a1a;
        border: 1px solid #FC4C02;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #FC4C02;
        font-family: 'Share Tech Mono', monospace;
    }
    .metric-label {
        font-size: 13px;
        color: #ffffff;
        font-family: 'Rajdhani', sans-serif;
        margin-top: 4px;
    }

    div[data-testid="stExpander"] {
        background-color: #1a1a1a;
        border: 1px solid #FC4C02;
        border-radius: 8px;
        color: #ffffff;
    }
    div[data-testid="stExpander"] > div { background-color: #1a1a1a !important; }
    div[data-testid="stExpanderDetails"] { background-color: #1a1a1a !important; }
    summary {
        background-color: #FC4C02 !important;
        border-radius: 6px;
        color: #ffffff !important;
        font-family: 'Share Tech Mono', monospace !important;
        padding: 10px 16px !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 1px solid #FC4C02 !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    .instrukcja {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 14px;
        margin-top: 16px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 13px;
        color: #aaaaaa;
    }
    .instrukcja a { color: #FC4C02 !important; }

    label { color: #ffffff !important; }
    .stCaption {
        color: #aaaaaa !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #1a1a1a;
        border-top: 1px solid #FC4C02;
        padding: 8px 24px;
        text-align: center;
        font-family: 'Share Tech Mono', monospace;
        font-size: 16px;
        color: #FC4C02;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# SESSION STATE
defaults = {
    "raport": None,
    "dane": None,
    "dane_json": None,
    "aktywnosci_surowe": None,
    "metryki": None,
    "dane_pobrane": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# SIDEBAR
with st.sidebar:
    try:
        logo = Image.open("AI_icon.png")
        st.image(logo, width=120)
    except Exception:
        st.write("🏃")

    st.markdown("## Asystent treningowy AI")
    st.caption("Analiza danych Strava + rekomendacje Gemini")
    st.divider()

    st.markdown("### Dane dostępowe")
    client_id = st.text_input("Strava Client ID")
    client_secret = st.text_input("Strava Client Secret", type="password")
    refresh_token = st.text_input("Strava Refresh Token", type="password")
    gemini_key = st.text_input("Gemini API Key", type="password")

    st.divider()
    st.markdown("### Zakres danych")
    tygodnie = st.slider("Ile tygodni historii pobrać ze Stravy?", min_value=4, max_value=24, value=12)

    st.divider()
    st.markdown("### Cel treningowy")
    cel = st.text_area(
        "Opisz swój cel",
        placeholder="np. Przygotowuję się do półmaratonu za 8 tygodni.",
        height=120
    )
    dni = st.slider("Dni treningowych w tygodniu", min_value=1, max_value=7, value=3)

    st.divider()
    pobierz_dane_btn = st.button("1. Pobierz dane ze Stravy", type="primary")
    analizuj_ai_btn = st.button("2. Wygeneruj analizę AI")

    st.markdown("""<div class="instrukcja">
    <b style="color:#FC4C02; font-size:15px">Nie wiesz jak zacząć?</b><br><br>
    🚴 <b>Strava</b><br>
    <a href="https://www.strava.com/settings/api" target="_blank">strava.com/settings/api</a><br><br>
    🤖 <b>Gemini</b><br>
    <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a><br>
    <span style="color:#FC4C02">Model: <b>gemini-2.5-flash</b></span><br><br>
    <span style="color:#888; font-size:12px">
    Aplikacja działa w dwóch krokach: najpierw pobiera dane ze Stravy, potem uruchamia analizę AI na żądanie.
    </span>
    </div>""", unsafe_allow_html=True)

# MAIN AREA
col_logo, col_title = st.columns([1, 6])
with col_logo:
    try:
        logo = Image.open("AI_icon.png")
        st.image(logo, width=80)
    except Exception:
        st.write("🏃")
with col_title:
    st.markdown("# Asystent treningowy AI")
    st.caption("Analiza Twoich danych treningowych ze Stravy i generowanie planu przez AI")

st.divider()


def pobierz_token(client_id, client_secret, refresh_token):
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        },
        timeout=30
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def pobierz_aktywnosci(access_token, tygodnie=12, max_stron=4):
    """
    Pobiera aktywności ze Stravy z paginacją.
    max_stron=4 i per_page=100 daje maksymalnie 400 aktywności.
    """
    data_od = int((datetime.now() - timedelta(weeks=tygodnie)).timestamp())
    wszystkie = []

    for page in range(1, max_stron + 1):
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "after": data_od,
                "per_page": 100,
                "page": page
            },
            timeout=30
        )

        if response.status_code != 200:
            return None

        aktywnosci = response.json()
        if not aktywnosci:
            break

        wszystkie.extend(aktywnosci)

    return wszystkie


def bezpieczna_wartosc(aktywnosc, pole, domyslnie="brak danych"):
    wartosc = aktywnosc.get(pole)
    if wartosc is None or wartosc == "":
        return domyslnie
    return wartosc


def formatuj_aktywnosci(aktywnosci):
    """
    Tworzy tekstowy opis aktywności dla Gemini.
    Pobiera szeroki zakres danych dostępnych na poziomie listy aktywności Strava.
    """
    if not aktywnosci:
        return None

    wynik = []

    for a in aktywnosci:
        dystans_km = round(a.get("distance", 0) / 1000, 2)
        czas_ruchu_min = round(a.get("moving_time", 0) / 60, 1)
        czas_calosci_min = round(a.get("elapsed_time", 0) / 60, 1)

        srednia_predkosc = a.get("average_speed")
        max_predkosc = a.get("max_speed")
        srednia_predkosc_kmh = round(srednia_predkosc * 3.6, 2) if srednia_predkosc is not None else "brak danych"
        max_predkosc_kmh = round(max_predkosc * 3.6, 2) if max_predkosc is not None else "brak danych"

        mapa = a.get("map", {}) or {}
        polyline = "dostępna" if mapa.get("summary_polyline") else "brak danych"

        wynik.append(
            f"- Data: {bezpieczna_wartosc(a, 'start_date_local', bezpieczna_wartosc(a, 'start_date'))} | "
            f"Nazwa: {a.get('name', 'Aktywność')} | "
            f"Typ: {a.get('type', '?')} | Sport type: {bezpieczna_wartosc(a, 'sport_type')} | "
            f"Workout type: {bezpieczna_wartosc(a, 'workout_type')} | "
            f"Dystans: {dystans_km} km | Czas ruchu: {czas_ruchu_min} min | "
            f"Czas całkowity: {czas_calosci_min} min | "
            f"Śr. prędkość: {srednia_predkosc_kmh} km/h | Maks. prędkość: {max_predkosc_kmh} km/h | "
            f"Przewyższenie: {bezpieczna_wartosc(a, 'total_elevation_gain')} m | "
            f"HR avg: {bezpieczna_wartosc(a, 'average_heartrate')} | HR max: {bezpieczna_wartosc(a, 'max_heartrate')} | "
            f"Kadencja: {bezpieczna_wartosc(a, 'average_cadence')} | Waty avg: {bezpieczna_wartosc(a, 'average_watts')} | "
            f"Kalorie: {bezpieczna_wartosc(a, 'calories')} | Suffer score: {bezpieczna_wartosc(a, 'suffer_score')} | "
            f"Osiągnięcia: {bezpieczna_wartosc(a, 'achievement_count')} | Kudos: {bezpieczna_wartosc(a, 'kudos_count')} | "
            f"Trenażer: {bezpieczna_wartosc(a, 'trainer')} | Dojazd: {bezpieczna_wartosc(a, 'commute')} | "
            f"Manualnie: {bezpieczna_wartosc(a, 'manual')} | Prywatne: {bezpieczna_wartosc(a, 'private')} | "
            f"Widoczność: {bezpieczna_wartosc(a, 'visibility')} | Sprzęt: {bezpieczna_wartosc(a, 'gear_id')} | "
            f"Strefa czasowa: {bezpieczna_wartosc(a, 'timezone')} | Mapa: {polyline}"
        )

    return "\n".join(wynik)


def przygotuj_json_aktywnosci(aktywnosci):
    wynik = []
    for a in aktywnosci:
        wynik.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "type": a.get("type"),
            "sport_type": a.get("sport_type"),
            "workout_type": a.get("workout_type"),
            "start_date": a.get("start_date"),
            "start_date_local": a.get("start_date_local"),
            "timezone": a.get("timezone"),
            "distance_km": round(a.get("distance", 0) / 1000, 2),
            "moving_time_min": round(a.get("moving_time", 0) / 60, 1),
            "elapsed_time_min": round(a.get("elapsed_time", 0) / 60, 1),
            "total_elevation_gain_m": a.get("total_elevation_gain"),
            "average_speed_kmh": round(a.get("average_speed", 0) * 3.6, 2) if a.get("average_speed") is not None else None,
            "max_speed_kmh": round(a.get("max_speed", 0) * 3.6, 2) if a.get("max_speed") is not None else None,
            "average_heartrate": a.get("average_heartrate"),
            "max_heartrate": a.get("max_heartrate"),
            "average_cadence": a.get("average_cadence"),
            "average_watts": a.get("average_watts"),
            "calories": a.get("calories"),
            "suffer_score": a.get("suffer_score"),
            "achievement_count": a.get("achievement_count"),
            "kudos_count": a.get("kudos_count"),
            "trainer": a.get("trainer"),
            "commute": a.get("commute"),
            "manual": a.get("manual"),
            "private": a.get("private"),
            "visibility": a.get("visibility"),
            "gear_id": a.get("gear_id"),
            "has_map_polyline": bool((a.get("map") or {}).get("summary_polyline"))
        })
    return wynik


def policz_metryki(aktywnosci):
    total_dystans = sum(a.get("distance", 0) for a in aktywnosci) / 1000
    total_czas = sum(a.get("moving_time", 0) for a in aktywnosci) / 3600
    typy = set((a.get("sport_type") or a.get("type") or "") for a in aktywnosci)
    total_przewyzszenie = sum(a.get("total_elevation_gain", 0) or 0 for a in aktywnosci)
    return round(total_dystans, 1), round(total_czas, 1), len(typy), round(total_przewyzszenie, 0)


def generuj_prompt(dane_treningowe, cel, dni, tygodnie):
    return f"""Jesteś doświadczonym trenerem personalnym i analitykiem danych treningowych.

Przeanalizuj poniższe dane treningowe użytkownika z ostatnich {tygodnie} tygodni i wygeneruj raport.

CEL UŻYTKOWNIKA:
{cel}

PREFEROWANA LICZBA DNI TRENINGOWYCH W TYGODNIU: {dni}

DANE TRENINGOWE:
{dane_treningowe}

Wygeneruj raport dokładnie w następujących sekcjach:

1. POZIOM AKTYWNOŚCI - oceń ogólny poziom aktywności użytkownika
2. POSTĘPY - zidentyfikuj trendy i postępy na podstawie danych
3. RYZYKO PRZECIĄŻENIA - oceń czy użytkownik nie trenuje za dużo lub za mało
4. SŁABE PUNKTY - wskaż obszary wymagające poprawy
5. PLAN NA 30 DNI - konkretny plan treningowy na kolejny miesiąc, tydzień po tygodniu, z podziałem na dni
6. CEL TYGODNIOWY - jeden główny cel na nadchodzący tydzień
7. REKOMENDACJE - 3 konkretne rekomendacje dopasowane do celu użytkownika
8. OCENA CELU - oceń czy cel użytkownika jest realistyczny w kontekście jego aktywności

WAŻNE ZASADY:
- Opieraj rekomendacje WYŁĄCZNIE na dostarczonych danych.
- Jeśli brakuje danych, np. tętna, kadencji, watów albo kalorii, zaznacz to i ogranicz rekomendacje.
- Nie zgaduj danych, których nie ma.
- Jeśli cel jest nieprecyzyjny, poproś o doprecyzowanie.
- Używaj języka polskiego.
- Nie stawiaj diagnoz medycznych.
- Zaznacz, że rekomendacje AI nie zastępują konsultacji z trenerem lub lekarzem.
- GUARDRAIL: Jeśli cel użytkownika nie jest związany z aktywnością fizyczną lub sportem, NIE generuj planu treningowego. Zamiast tego napisz krótką informację, że aplikacja służy wyłącznie do analizy treningowej i poproś o podanie celu sportowego.
"""


def parsuj_sekcje(tekst):
    nazwy_sekcji = [
        "1. POZIOM AKTYWNOŚCI",
        "2. POSTĘPY",
        "3. RYZYKO PRZECIĄŻENIA",
        "4. SŁABE PUNKTY",
        "5. PLAN NA 30 DNI",
        "6. CEL TYGODNIOWY",
        "7. REKOMENDACJE",
        "8. OCENA CELU"
    ]
    sekcje = []
    for i, nazwa in enumerate(nazwy_sekcji):
        start = tekst.find(nazwa)
        if start == -1:
            continue
        if i + 1 < len(nazwy_sekcji):
            koniec = tekst.find(nazwy_sekcji[i + 1])
            if koniec == -1:
                koniec = len(tekst)
        else:
            koniec = len(tekst)
        tresc = tekst[start + len(nazwa):koniec].strip()
        tresc = re.sub(r'^#+\s*', '', tresc, flags=re.MULTILINE)
        sekcje.append((nazwa, tresc))
    return sekcje


# KROK 1: POBIERANIE DANYCH ZE STRAVY
if pobierz_dane_btn:
    st.session_state.raport = None

    if not client_id or not client_secret or not refresh_token:
        st.error("Uzupełnij dane dostępowe Strava w panelu bocznym.")
    else:
        with st.spinner("Autoryzacja Strava..."):
            token = pobierz_token(client_id, client_secret, refresh_token)

        if not token:
            st.error("Błąd autoryzacji Strava. Sprawdź dane dostępowe. [W1]")
        else:
            with st.spinner("Pobieranie aktywności ze Stravy..."):
                aktywnosci = pobierz_aktywnosci(token, tygodnie=tygodnie)

            if not aktywnosci:
                st.error(f"Brak aktywności w ostatnich {tygodnie} tygodniach albo błąd pobierania danych. [W2]")
            else:
                dane = formatuj_aktywnosci(aktywnosci)
                dane_json = przygotuj_json_aktywnosci(aktywnosci)
                dystans, czas, typy, przewyzszenie = policz_metryki(aktywnosci)

                st.session_state.aktywnosci_surowe = aktywnosci
                st.session_state.dane = dane
                st.session_state.dane_json = dane_json
                st.session_state.metryki = (len(aktywnosci), dystans, czas, typy, przewyzszenie, tygodnie)
                st.session_state.dane_pobrane = True

                st.success("Dane ze Stravy zostały pobrane. Możesz teraz uruchomić analizę AI.")


# KROK 2: ANALIZA AI ON DEMAND
if analizuj_ai_btn:
    if not st.session_state.dane_pobrane or not st.session_state.dane:
        st.error("Najpierw pobierz dane ze Stravy przyciskiem: 1. Pobierz dane ze Stravy.")
    elif not gemini_key:
        st.error("Podaj klucz Gemini API w panelu bocznym.")
    elif not cel:
        st.error("Opisz swój cel treningowy w panelu bocznym.")
    else:
        with st.spinner("Trwa analiza AI..."):
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = generuj_prompt(st.session_state.dane, cel, dni, st.session_state.metryki[5])
                response = model.generate_content(prompt)
                st.session_state.raport = response.text
                st.success("Raport AI został wygenerowany.")
            except Exception as e:
                if "429" in str(e):
                    st.warning("⏳ Przekroczono limit zapytań Gemini API. Poczekaj chwilę i spróbuj ponownie.")
                else:
                    st.error(f"Błąd Gemini API. Sprawdź klucz API. [W3] ({str(e)})")


# WYŚWIETLANIE POBRANYCH DANYCH
if st.session_state.dane_pobrane and st.session_state.metryki:
    liczba, dystans, czas, typy, przewyzszenie, zakres_tygodni = st.session_state.metryki

    col_reset, col_empty = st.columns([1, 5])
    with col_reset:
        if st.button("🔄 Wyczyść dane"):
            st.session_state.raport = None
            st.session_state.dane = None
            st.session_state.dane_json = None
            st.session_state.aktywnosci_surowe = None
            st.session_state.metryki = None
            st.session_state.dane_pobrane = False
            st.rerun()

    st.markdown(f"### Twoje statystyki z ostatnich {zakres_tygodni} tygodni")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{liczba}</div><div class="metric-label">Aktywności</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{dystans} km</div><div class="metric-label">Łączny dystans</div></div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{czas} h</div><div class="metric-label">Łączny czas</div></div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{typy}</div><div class="metric-label">Typy aktywności</div></div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{przewyzszenie} m</div><div class="metric-label">Przewyższenie</div></div>""", unsafe_allow_html=True)

    st.divider()

    st.download_button(
        label="Pobierz pobrane dane jako JSON",
        data=json.dumps(st.session_state.dane_json, ensure_ascii=False, indent=2),
        file_name=f"dane_strava_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json"
    )


# WYŚWIETLANIE RAPORTU AI
if st.session_state.raport:
    st.divider()
    st.markdown("### Twój raport treningowy")

    sekcje = parsuj_sekcje(st.session_state.raport)

    if sekcje:
        for nazwa, tresc in sekcje:
            st.markdown(f"**{nazwa}**")
            with st.expander("rozwiń", expanded=False):
                st.markdown(tresc)
    else:
        st.markdown(st.session_state.raport)

    st.divider()
    st.download_button(
        label="Pobierz raport jako TXT",
        data=st.session_state.raport,
        file_name=f"raport_treningowy_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# STOPKA
st.markdown("""
<div class="footer">
    ⚡ Prototyp — Projekt dyplomowy MOSTY AI | Asystent treningowy AI | Strava + Gemini | Wykonanie: Marta Ptaszynska
</div>
""", unsafe_allow_html=True)
