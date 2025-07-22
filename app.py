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
st.image(logo_path, width=300)
st.markdown("## Sofies Tidsmaskin")

# 📦 Session state for historikk
if "story_data" not in st.session_state:
    st.session_state.story_data = {}
if "historie_generert" not in st.session_state:
    st.session_state.historie_generert = False
if "sporsmal" not in st.session_state:
    st.session_state.sporsmal = []
if "image_url" not in st.session_state:
    st.session_state.image_url = None

# 🧾 Brukerinput
if not st.session_state.historie_generert:
    date = st.text_input("Skriv inn dato (DD.MM.ÅÅÅÅ)", placeholder="f.eks. 01.05.1945")
    location = st.text_input("Skriv inn sted/land", placeholder="f.eks. Berlin, Tyskland")
    navn = st.text_input("Skriv inn ditt navn")
    samfunnslag = st.text_input("Hvilket samfunnslag kommer de fra? (valgfritt)", placeholder="f.eks. arbeiderklasse, adelen, bønder, middelklasse")
    etnisitet = st.text_input("Hva slags etnisitet har ungdommene? (valgfritt)", placeholder="f.eks. tysk, norsk, afrikansk-amerikansk")

    if st.button("Fortell meg en historie"):
        if not date or not location or not navn:
            st.warning("Skriv inn både dato, sted og navn for å komme i gang.")
        else:
            with st.spinner("Reiser tilbake i tid..."):
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
- Være **kort og konsis** (maks 500–600 ord), og egnet for ungdom i alderen 16–18 år.
- Inneholde en **drivende konflikt eller dramatisk hendelse** – noe som overrasker eller utfordrer hovedpersonen.
- Ha en tydelig **"wow-faktor"** – noe som gjør at leseren tenker: *"Hæ?! Skjedde DET?!"*
- Inneholde **realistiske og sanselige detaljer** fra tid og sted: arbeid, skole (bare hvis realistisk), familie, samfunn, kultur, politikk.
- Ha en ungdommelig fortellerstil: direkte, ekte og følelsesnær – **unngå overdreven poesi og lange metaforer**.
- Avsluttes med noen kloke, rørende eller inspirerende ord – som gir eleven noe å tenke på.
- Personen takker til slutt Sofie og brukeren for besøket.

🫭 Viktige regler:
- Sofie snakker ikke – hun er bare med på reisen.
- Ikke forklar, oppsummer eller si "Her kommer en historie om...". Gå rett inn i fortellingen med personens første replikk.
- Ikke bruk moderne ord, uttrykk eller konsepter som ikke fantes i perioden (f.eks. plast, strøm, dorullskip).
- Ikke referer til Øksnevad vgs eller andre moderne institusjoner.
Historien foregår i {location} den {date}.
"""

                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du er en historieforteller med ungdommelig og sanselig stil, inspirert av varme og realisme. Du skriver i jeg-form og lar en ungdom fortelle en levende og følelsesnær historie fra sitt liv, basert på tid og sted. Historien starter med personlig hilsen og skal være lang, detaljert og fri for skrivefeil."},
                        {"role": "user", "content": story_prompt}
                    ],
                    max_tokens=3000
                )

                story = response.choices[0].message.content
                image_prompt = f"Realistic portrait of a young girl named {navn} from {location} in {date}, {etnisitet if etnisitet else 'local'} ethnicity, historical outfit from that era, expressive face, visible cinematic background of {location}, ultra-detailed, photorealistic"

                image_response = openai.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    n=1,
                    size="1024x1024"
                )

                st.session_state.image_url = image_response.data[0].url
                st.session_state.story_data = {
                    "location": location,
                    "date": date,
                    "story": story,
                    "samfunnslag": samfunnslag,
                    "etnisitet": etnisitet,
                    "navn": navn
                }
                st.session_state.historie_generert = True
                st.rerun()

# 📖 Vis historie og bilde
else:
    st.markdown(f"#### {st.session_state.story_data['date']} – {st.session_state.story_data['location']}")
    st.text_area("Historien:", st.session_state.story_data['story'], height=500)

    if st.session_state.image_url:
        st.image(st.session_state.image_url, caption="Et glimt fra reisen", use_container_width=True)

    if st.button("🔁 Lag en ny historie"):
        st.session_state.historie_generert = False
        st.session_state.story_data = {}
        st.session_state.sporsmal = []
        st.session_state.image_url = None
        st.rerun()

    if st.button("Last ned som PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            c = canvas.Canvas(tmpfile.name, pagesize=A4)
            text = c.beginText(2 * cm, 28 * cm)
            text.setFont("Times-Roman", 12)
            for linje in st.session_state.story_data['story'].split("\n"):
                if text.getY() < 2 * cm:
                    c.drawText(text)
                    c.showPage()
                    text = c.beginText(2 * cm, 28 * cm)
                    text.setFont("Times-Roman", 12)
                text.textLine(linje)
            c.drawText(text)
            c.save()

            with open(tmpfile.name, "rb") as f:
                st.download_button("📄 Last ned historien som PDF", f, file_name="sofies_tidsreise.pdf")
