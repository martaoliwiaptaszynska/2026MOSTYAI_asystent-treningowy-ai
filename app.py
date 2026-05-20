import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
from PIL import Image
import re

st.set_page_config(
    page_title="Asystent treningowy AI",
    page_icon="🏃",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600&display=swap');

    .stApp {
        background-color: #0f0f0f;
        color: #ffffff;
    }

    header[data-testid="stHeader"] {
        background-color: #0f0f0f !important;
        border-bottom: 1px solid #FC4C02;
    }
    #MainMenu, footer, header .stDeployButton {
        visibility: hidden;
    }

    h1, h2, h3, h4 {
        font-family: 'Share Tech Mono', monospace !important;
        color: #FC4C02 !important;
    }
    p, li, span, label, .stMarkdown {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 16px !important;
        color: #ffffff !important;
    }

    .stSidebar {
        background-color: #1a1a1a;
    }
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
    .stButton > button:hover {
        background-color: #e04400;
    }

    .stDownloadButton > button {
        background-color: #FC4C02 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-weight: bold !important;
        padding: 12px !important;
    }
    .stDownloadButton > button:hover {
        background-color: #e04400 !important;
    }

    .metric-card {
        background-color: #1a1a1a;
        border: 1px solid #FC4C02;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
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
    div[data-testid="stExpander"] > div {
        background-color: #1a1a1a !important;
    }
    div[data-testid="stExpanderDetails"] {
        background-color: #1a1a1a !important;
    }
    summary {
        background-color: #FC4C02 !important;
        border-radius: 6px;
        color: #ffffff !important;
        font-family: 'Share Tech Mono', monospace !important;
        padding: 10px 16px !important;
    }

    [data-testid="stExpanderToggleIcon"] {
        display: none !important;
    }
    details summary > span:first-child {
        display: none !important;
    }
    .st-emotion-cache-sh2krr {
        display: none !important;
    }
    summary p {
        display: none !important;
    }
    summary svg {
        display: none !important;
    }

    .stTextInput > div > div > input {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 1px solid #FC4C02 !important;
        font-family: 'Rajdhani', sans-serif !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #888888 !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #2a2a2a !important;
        color: #ffffff !important;
        border: 1px solid #FC4C02 !important;
        font-family: 'Rajdhani', sans-serif !important;
    }
    .stTextArea > div > div > textarea::placeholder {
        color: #888888 !important;
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
    .instrukcja a {
        color: #FC4C02 !important;
    }

    .stSlider > div {
        color: #ffffff !important;
    }
    label {
        color: #ffffff !important;
    }
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
if "raport" not in st.session_state:
    st.session_state.raport = None
if "dane" not in st.session_state:
    st.session_state.dane = None
if "metryki" not in st.session_state:
    st.session_state.metryki = None

# SIDEBAR
with st.sidebar:
    try:
        logo = Image.open("AI_icon.png")
        st.image(logo, width=120)
    except:
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
    st.markdown("### Cel treningowy")
    cel = st.text_area(
        "Opisz swój cel",
        placeholder="np. Przygotowuję się do półmaratonu za 8 tygodni.",
        height=120
    )
    dni = st.slider("Dni treningowych w tygodniu", min_value=1, max_value=7, value=3)

    st.divider()
    analiza = st.button("Analizuj i generuj plan", type="primary")

    st.markdown("""<div class="instrukcja">
    <b style="color:#FC4C02; font-size:15px">Nie wiesz jak zacząć?</b><br><br>
    Potrzebujesz dwóch kluczy API:<br><br>
    🚴 <b>Strava</b><br>
    <a href="https://www.strava.com/settings/api" target="_blank">strava.com/settings/api</a><br>
    Utwórz aplikację → skopiuj Client ID, Client Secret i Refresh Token<br><br>
    🤖 <b>Gemini</b><br>
    <a href="https://aistudio.google.com/apikey" target="_blank">aistudio.google.com/apikey</a><br>
    Zaloguj się → Create API Key → skopiuj klucz<br>
    <span style="color:#FC4C02">Wymagany model: <b>gemini-2.5-flash</b></span><br>
    <span style="color:#888; font-size:12px">Darmowy tier: 5 zapytań/min — odczekaj chwilę między analizami.</span><br><br>
    <hr style="border-color:#333; margin:10px 0">
    <span style="color:#888; font-size:12px">
    To jest prototyp — funkcjonalności będą rozwijane.<br>
    Dane nie są zapisywane i są aktywne tylko podczas sesji.
    </span>
    </div>""", unsafe_allow_html=True)

# MAIN AREA
col_logo, col_title = st.columns([1, 6])
with col_logo:
    try:
        logo = Image.open("AI_icon.png")
        st.image(logo, width=80)
    except:
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
        }
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def pobierz_aktywnosci(access_token, tygodnie=4):
    data_od = int((datetime.now() - timedelta(weeks=tygodnie)).timestamp())
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"after": data_od, "per_page": 50}
    )
    if response.status_code == 200:
        return response.json()
    return None

def formatuj_aktywnosci(aktywnosci):
    if not aktywnosci:
        return None
    wynik = []
    for a in aktywnosci:
        dystans_km = round(a.get("distance", 0) / 1000, 2)
        czas_min = round(a.get("moving_time", 0) / 60, 1)
        tetno = a.get("average_heartrate", "brak danych")
        wynik.append(
            f"- {a.get('name', 'Aktywność')} | {a.get('type', '?')} | "
            f"{dystans_km} km | {czas_min} min | HR: {tetno}"
        )
    return "\n".join(wynik)

def policz_metryki(aktywnosci):
    total_dystans = sum(a.get("distance", 0) for a in aktywnosci) / 1000
    total_czas = sum(a.get("moving_time", 0) for a in aktywnosci) / 3600
    typy = set(a.get("type", "") for a in aktywnosci)
    return round(total_dystans, 1), round(total_czas, 1), len(typy)

def generuj_prompt(dane_treningowe, cel, dni):
    return f"""Jesteś doświadczonym trenerem personalnym i analitykiem danych treningowych.

Przeanalizuj poniższe dane treningowe użytkownika z ostatnich 4 tygodni i wygeneruj raport.

CEL UŻYTKOWNIKA:
{cel}

PREFEROWANA LICZBA DNI TRENINGOWYCH W TYGODNIU: {dni}

DANE TRENINGOWE (format: nazwa | typ | dystans | czas | tętno):
{dane_treningowe}

Wygeneruj raport w następujących sekcjach:

1. POZIOM AKTYWNOŚCI - oceń ogólny poziom aktywności użytkownika
2. POSTĘPY - zidentyfikuj trendy i postępy na podstawie danych
3. RYZYKO PRZECIĄŻENIA - oceń czy użytkownik nie trenuje za dużo lub za mało
4. SŁABE PUNKTY - wskaż obszary wymagające poprawy
5. PLAN NA 7 DNI - konkretny plan treningowy na kolejny tydzień (dzień po dniu)
6. CEL TYGODNIOWY - jeden główny cel na nadchodzący tydzień
7. REKOMENDACJE - 3 konkretne rekomendacje dopasowane do celu użytkownika
8. OCENA CELU - oceń czy cel użytkownika jest realistyczny w kontekście jego aktywności

WAŻNE ZASADY:
- Opieraj rekomendacje WYŁĄCZNIE na dostarczonych danych
- Jeśli brakuje danych (np. brak tętna), zaznacz to i ogranicz rekomendacje
- Nie zgaduj danych których nie ma
- Jeśli cel jest nieprecyzyjny, poproś o doprecyzowanie
- Używaj języka polskiego
- GUARDRAIL: Jeśli cel użytkownika nie jest związany z aktywnością fizyczną lub sportem (np. cele finansowe, zawodowe, osobiste), NIE generuj planu treningowego. Zamiast tego napisz krótką informację że aplikacja służy wyłącznie do analizy treningowej i poproś o podanie celu sportowego.
"""

def parsuj_sekcje(tekst):
    nazwy_sekcji = [
        "1. POZIOM AKTYWNOŚCI",
        "2. POSTĘPY",
        "3. RYZYKO PRZECIĄŻENIA",
        "4. SŁABE PUNKTY",
        "5. PLAN NA 7 DNI",
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

if analiza:
    print(">>> KLIKNIĘTO PRZYCISK")
    if not client_id or not client_secret or not refresh_token:
        st.error("Uzupełnij dane dostępowe Strava w panelu bocznym.")
    elif not gemini_key:
        st.error("Podaj klucz Gemini API w panelu bocznym.")
    elif not cel:
        st.error("Opisz swój cel treningowy w panelu bocznym.")
    else:
        with st.spinner("Pobieranie danych ze Strava..."):
            token = pobierz_token(client_id, client_secret, refresh_token)
        if not token:
            st.error("Błąd autoryzacji Strava. Sprawdź dane dostępowe. [W1]")
        else:
            with st.spinner("Pobieranie aktywności..."):
                aktywnosci = pobierz_aktywnosci(token)
            if not aktywnosci:
                st.error("Brak aktywności w ostatnich 4 tygodniach. [W2]")
            else:
                dane = formatuj_aktywnosci(aktywnosci)
                dystans, czas, typy = policz_metryki(aktywnosci)
                st.session_state.metryki = (len(aktywnosci), dystans, czas, typy)
                st.session_state.dane = dane
                with st.spinner("Trwa analiza AI..."):
                    try:
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        prompt = generuj_prompt(dane, cel, dni)
                        print(">>> WYSYŁAM ZAPYTANIE DO GEMINI")
                        response = model.generate_content(prompt)
                        print(">>> GEMINI ODPOWIEDZIAŁ")
                        st.session_state.raport = response.text
                    except Exception as e:
                        print(f">>> BŁĄD: {str(e)[:100]}")
                        if "429" in str(e):
                            st.warning("⏳ Przekroczono limit zapytań Gemini API (5 zapytań/min). Poczekaj 30 sekund i spróbuj ponownie.")
                        else:
                            st.error(f"Błąd Gemini API. Sprawdź klucz API. [W3] ({str(e)})")

# WYSWIETL WYNIKI z session state
if st.session_state.raport:

    col_reset, col_empty = st.columns([1, 5])
    with col_reset:
        if st.button("🔄 Nowa analiza"):
            st.session_state.raport = None
            st.session_state.dane = None
            st.session_state.metryki = None
            st.rerun()

    liczba, dystans, czas, typy = st.session_state.metryki
    st.markdown("### Twoje statystyki z ostatnich 4 tygodni")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{liczba}</div>
            <div class="metric-label">Aktywności</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{dystans} km</div>
            <div class="metric-label">Łączny dystans</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{czas} h</div>
            <div class="metric-label">Łączny czas</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{typy}</div>
            <div class="metric-label">Typy aktywności</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    with st.expander("Zobacz pobrane dane"):
        st.text(st.session_state.dane)

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
