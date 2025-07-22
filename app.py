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
- Være troverdig for tid og sted, med sanselige detaljer fra hverdagsliv, arbeid, familie, skole (kun hvis realistisk for personens klasse og tid), kultur, politikk og økonomi.
- Ikke bruke moderne ord, begreper eller uttrykk som ikke eksisterte i perioden – som \"dorullskip\", plastleker eller referanser til nåtidige konsepter.
- Inneholde uventede, spennende eller tankevekkende elementer – noe som vekker undring eller følelser hos Sofie og brukeren.
- Avsluttes med noen kloke, rørende eller innsiktsfulle ord, som gir leseren noe å tenke på.
- Personen takker deretter Sofie og brukeren for besøket.

🧭 Viktige regler:
- Sofie snakker ikke – hun er bare med på reisen.
- Ikke forklar, oppsummer eller si \"Her kommer en historie om...\". Gå rett inn i fortellingen med personens første replikk.
- Språket skal være ungdomsnært, sanselig og fortellende – ikke som et leksikon. Det skal føles som å høre noen fortelle rett til deg.
- Ikke referer til Øksnevad vgs eller andre moderne institusjoner.
Historien foregår i {location} den {date}.
"""

                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du er en historieforteller med ungdommelig og sanselig stil, inspirert av varme og realisme. Du skriver i jeg-form og lar en ungdom fortelle en levende og følelsesnær historie fra sitt liv, basert på tid og sted. Historien starter med personlig hilsen og avsluttes med visdomsord og hilsen."},
                        {"role": "user", "content": story_prompt}
                    ],
                    max_tokens=3000
                )

                story = response.choices[0].message.content
                image_prompt = f"Portrait of a {etnisitet if etnisitet else 'local'} youth from {location} in {date}, with visible historical surroundings, realistic style"

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
    st.text_area("Historien:", st.session_state.story_data['story'], height=400)

    if st.session_state.image_url:
        st.image(st.session_state.image_url, caption="Et glimt fra reisen", use_column_width=True)

    nytt_spm = st.text_input("Still et oppfølgingsspørsmål")
    if st.button("Still spørsmål"):
        if nytt_spm:
            follow_up_prompt = f"Bruk samme stil og forteller som forrige historie, og svar på dette oppfølgingsspørsmålet: '{nytt_spm}'"
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": follow_up_prompt}
                ],
                max_tokens=1000
            )
            st.session_state.sporsmal.append((nytt_spm, response.choices[0].message.content))
            st.rerun()

    for idx, (spm, svar) in enumerate(st.session_state.sporsmal):
        st.markdown(f"**Spørsmål {idx+1}:** {spm}")
        st.markdown(f"{svar}")

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

    if st.button("🔁 Lag en ny historie"):
        st.session_state.historie_generert = False
        st.session_state.story_data = {}
        st.session_state.sporsmal = []
        st.session_state.image_url = None
        st.rerun()
