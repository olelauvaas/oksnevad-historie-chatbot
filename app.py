import streamlit as st
import os
import openai
from PIL import Image
import requests
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# 🔐 OpenAI API-nøkkel fra secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = openai.api_key

# 🎨 Streamlit-oppsett
st.set_page_config(page_title="Sofies Tidsmaskin")
logo_path = "logo.PNG"
st.image(logo_path, width=300, use_container_width=False)
st.markdown("## Sofies Tidsmaskin")

st.markdown("""
### 🧱 Velkommen til Sofies tidsmaskin
Du er på vei tilbake i tid.

Sammen med Sofie skal du besøke et sted i verden på et bestemt tidspunkt i historien. Der møter du en ungdom som forteller deg hvordan det er å leve akkurat der og da – med sine egne ord.

🔹 Det du skal gjøre:
Skriv inn:
- Navnet ditt
- Dato (f.eks. 18.08.1894)
- Sted og land (f.eks. Bridgetown, Barbados)
- (Valgfritt) etnisitet og samfunnslag

Les historien nøye.
Du får møte en ungdom som forteller om sitt liv, utfordringer, drømmer og samfunnet rundt seg.

Etterpå skal du tenke over:
- Hva lærte du om perioden?
- Hvilke spor av historie kjenner du igjen?
- Hva overrasket deg?

🧠 Husk:
– Det du leser, er en fiksjon basert på historiske forhold.
– Fortellingen er skrevet for å hjelpe deg å forstå tiden gjennom menneskene som levde i den.
– Ingen magi. Ingen roboter. Bare ekte mennesker, ekte liv – slik det kunne ha vært.
""")

# 📦 Session state for historikk
if "story_data" not in st.session_state:
    st.session_state.story_data = {}

# 🧾 Brukerinput
if "historie_generert" not in st.session_state or not st.session_state.historie_generert:
    navn = st.text_input("Hva heter du?", placeholder="f.eks. Sofie")
    date = st.text_input("Dato (DD.MM.ÅÅÅÅ)", placeholder="f.eks. 01.05.1897")
    location = st.text_input("Sted og land", placeholder="f.eks. Bridgetown, Barbados")
    extra_details = st.text_input("(Valgfritt) Etnisitet og samfunnslag", placeholder="f.eks. afro-karibisk, arbeiderklasse")

    if st.button("Reis i tid") and navn and date and location:

        story_prompt = f"""
🛠️ Systemprompt til GPT: Sofies tidsmaskin

Du er en historiefortellende GPT kalt Sofies tidsmaskin. Brukeren har skrevet inn sitt navn, en dato, et årstall, et sted og et land. Du skal nå ta med brukeren og Sofie (en fiktiv kvinnelig tidsreisepartner) tilbake i tid til dette stedet og tidspunktet.

🎭 Rollen din:
Når dere ankommer, blir dere møtt av en lokal ungdom, som har fått et tilfeldig navn. Hun er den som forteller historien. Hun skal:

- Henvende seg direkte til både Sofie og {navn} i åpningsreplikken.
- Presentere seg med navn og alder.
- Dersom etnisitet og samfunnslag ikke er angitt av brukeren, skal du selv velge og nevne dette tidlig i historien på en naturlig måte.
- Snakke i jeg-form og fortelle en personlig og levende historie om hvordan det er å leve akkurat her og nå.

📜 Historien skal:
- Være **faglig troverdig** basert på tid og sted (årstall, kultur, klasse, samfunn).
- Ha **maks 500–600 ord** – kort nok for ungdom og undervisning.
- Inneholde **én personlig utfordring eller hendelse** som er dramatisk, overraskende eller tankevekkende – men **alltid realistisk** for perioden.
- Inkludere konkrete beskrivelser av hverdagsliv: arbeid, familie, utdanning (hvis relevant), religion, økonomi, politikk, lokale hendelser og relasjoner.
- Språket skal være **ungdommelig og sanselig**, men ikke overdrevent poetisk.
- **Ingen moderne konsepter eller teknologi** må nevnes – og **ikke fantasy, magi eller overnaturlige elementer**.
- Avsluttes med noen reflektive eller inspirerende ord, og en personlig takk til Sofie og brukeren for besøket.

🧭 Viktige regler:
- Sofie snakker ikke – hun er bare med på reisen.
- Ikke skriv “Her kommer en historie om…” – gå rett inn i handlingen med personens replikk.
- Ikke bruk moderne uttrykk, teknologi eller referanser etter tidsepoken.
- Ikke nevne GPT, datamaskiner, kunstig intelligens, eller skoler som Øksnevad vgs.
Historien foregår i {location} den {date}.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": story_prompt},
                {"role": "user", "content": "Fortell historien."}
            ]
        )

        story = response.choices[0].message.content
        st.session_state.story_data = {
            "story": story,
            "navn": navn,
            "date": date,
            "location": location
        }

        # 🔍 Generer bilde
        dalle_prompt = f"Portrait of a teenage girl from {extra_details if extra_details else 'local community'} in {location} in the year {date[-4:]}, realistic style, detailed, standing in historical setting"
        dalle_response = openai.Image.create(
            prompt=dalle_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = dalle_response['data'][0]['url']
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))

        st.session_state.story_data["image"] = image
        st.session_state.historie_generert = True
        st.rerun()

# 📝 Vis historien
else:
    st.markdown("---")
    st.markdown(f"### 📖 Historien din: {st.session_state.story_data['location']} {st.session_state.story_data['date']}")
    st.image(st.session_state.story_data["image"], caption="Din tidsreisevenn", use_column_width=True)
    st.markdown(st.session_state.story_data["story"])

    # 📄 Lag PDF
    if st.button("📥 Last ned som PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=A4)
            textobject = c.beginText(2 * cm, 27.7 * cm)
            textobject.setFont("Helvetica", 12)
            for line in st.session_state.story_data["story"].split("\n"):
                textobject.textLine(line)
            c.drawText(textobject)
            c.save()

            with open(tmp.name, "rb") as f:
                st.download_button("📩 Klikk her for å laste ned historien som PDF", f, file_name="sofies_tidsreise.pdf")

    if st.button("⏮️ Start på nytt"):
        st.session_state.historie_generert = False
        st.session_state.story_data = {}
        st.rerun()
