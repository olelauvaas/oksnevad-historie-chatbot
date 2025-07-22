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

# 🧾 Brukerinput
if "historie_generert" not in st.session_state or not st.session_state.historie_generert:
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
- Presentere seg med navn, alder, og dersom det ikke allerede er spesifisert i prompten: også etnisitet og hvilket samfunnslag hun tilhører.
- Snakke i jeg-form og fortelle en personlig og levende historie om hvordan det er å leve akkurat her og nå.

📜 Historien skal:
- Være troverdig for tid og sted, med sanselige detaljer fra hverdagsliv, arbeid, familie, skole, kultur, politikk og økonomi.
- Inneholde uventede, spennende eller tankevekkende elementer – noe som vekker undring eller følelser hos Sofie og brukeren.
- Avsluttes med noen kloke, rørende eller innsiktsfulle ord, som gir leseren noe å tenke på.
- Personen takker deretter Sofie og brukeren for besøket.

🧭 Viktige regler:
- Sofie snakker ikke – hun er bare med på reisen.
- Ikke forklar, oppsummer eller si "Her kommer en historie om...". Gå rett inn i fortellingen med personens første replikk.
- Dersom etnisitet og samfunnslag ikke er nevnt av brukeren, skal du selv velge og oppgi dette naturlig i introduksjonen.
- Språket skal være ungdomsnært, sanselig og fortellende – ikke som et leksikon. Det skal føles som å høre noen fortelle rett til deg.
Historien foregår i {location} den {date}.
"""

                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du er en historieforteller med ungdommelig og sanselig stil, inspirert av varme og realisme. Du skriver i jeg-form og lar en ungdom fortelle en levende og følelsesnær historie fra sitt liv, basert på tid og sted. Historien starter med personlig hilsen og avsluttes med visdomsord og hilsen til Øksnevad vgs."},
                        {"role": "user", "content": story_prompt}
                    ],
                    max_tokens=3000
                )

                story = response.choices[0].message.content
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

# 📄 PDF-funksjon

def lag_pdf(tittel, tekst, bilde_path=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, 28 * cm, tittel)
    y = 27 * cm
    if bilde_path and os.path.exists(bilde_path):
        try:
            c.drawImage(bilde_path, 2 * cm, y - 12 * cm, width=12 * cm, height=12 * cm, preserveAspectRatio=True)
            y -= 13 * cm
        except Exception as e:
            print("Kunne ikke legge til bilde i PDF:", e)
    c.setFont("Helvetica", 12)
    for linje in tekst.split("\n"):
        linje = linje.strip()
        if not linje:
            y -= 0.6 * cm
            continue
        while linje:
            if y < 2 * cm:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 27 * cm
            cut = linje[:100]
            c.drawString(2 * cm, y, cut)
            linje = linje[100:]
            y -= 0.6 * cm
    c.save()
    return temp_file.name

# 📸 Bildeprompt

def generer_bildeprompt(location, date, samfunnslag, etnisitet):
    try:
        year = int(date.split(".")[-1])
    except:
        year = 1950
    stil = "realistic, cinematic lighting, emotionally expressive, historically accurate, background clearly shows environment, character present but not dominating"
    if year < 1920:
        stil += ", sepia tone, Edwardian clothing"
    elif year < 1950:
        stil += ", 1940s attire, monochrome"
    elif year < 1980:
        stil += ", 1970s youth, warm tones"
    elif year < 2000:
        stil += ", 1990s teenager, nostalgic mood"
    if samfunnslag:
        stil += f", depicting {samfunnslag} background"
    if etnisitet:
        stil += f", {etnisitet}"
    prompt = f"teenager (16–18), in {location} on {date}, {stil}"
    return prompt

# 📚 Vis historie
if st.session_state.get("historie_generert"):
    data = st.session_state.story_data
    st.markdown("### Her er historien:")
    st.markdown(data["story"])

    # Bilde og PDF
    if "bilde_url" not in data:
        with st.spinner("Genererer bilde..."):
            image_prompt = generer_bildeprompt(data["location"], data["date"], data["samfunnslag"], data["etnisitet"])
            try:
                image_response = openai.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    n=1,
                    size="1024x1024"
                )
                image_url = image_response.data[0].url
                image = Image.open(BytesIO(requests.get(image_url).content))
                st.image(image, caption=f"{data['location']}, {data['date']}")
                temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                image.save(temp_image_file.name)
                data["bilde_url"] = image_url
                data["bilde_path"] = temp_image_file.name
            except Exception as e:
                st.error("Bilde kunne ikke genereres.")
                data["bilde_url"] = None
                data["bilde_path"] = None

    pdf_fil = lag_pdf(f"Historien fra {data['location']} den {data['date']}", data["story"], data.get("bilde_path"))
    with open(pdf_fil, "rb") as f:
        st.download_button(
            label="\U0001F4C4 Last ned historien som PDF (med bilde)",
            data=f,
            file_name=f"historie_{data['location']}_{data['date']}.pdf",
            mime="application/pdf"
        )

    if st.button("Lag en ny historie"):
        st.session_state.historie_generert = False
        st.rerun()
