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
st.set_page_config(page_title="Historiefortelleren", page_icon="\U0001F4D6")
st.title("\U0001F4D6 Historiefortelleren – reis i tid med AI")

# 📦 Session state for historikk og spørsmål
if "story_data" not in st.session_state:
    st.session_state.story_data = {}

# 🧾 Brukerinput
if "historie_generert" not in st.session_state or not st.session_state.historie_generert:
    date = st.text_input("Skriv inn dato (DD.MM.ÅÅÅÅ)", placeholder="f.eks. 01.05.1945")
    location = st.text_input("Skriv inn sted/land", placeholder="f.eks. Berlin, Tyskland")
    boy_name = st.text_input("Navn på gutten (valgfritt)")
    girl_name = st.text_input("Navn på jenta (valgfritt)")
    samfunnslag = st.text_input("Hvilket samfunnslag kommer de fra? (valgfritt)", placeholder="f.eks. arbeiderklasse, adelen, bønder, middelklasse")
    etnisitet = st.text_input("Hva slags etnisitet har ungdommene? (valgfritt)", placeholder="f.eks. tysk, norsk, afrikansk-amerikansk")

    if st.button("Fortell meg en historie"):
        if not date or not location:
            st.warning("Skriv inn både dato og sted for å komme i gang.")
        else:
            with st.spinner("Reiser tilbake i tid..."):
                story_prompt = f"""
Skriv en realistisk og engasjerende historie satt til {location} den {date}.

Når eleven fra Øksnevad vgs ankommer som en tidsreisende, møter de to ungdommer (ca. 16–18 år) som er kjærester:
- {'gutten heter ' + boy_name if boy_name else 'du velger navnet på gutten'}
- {'jenta heter ' + girl_name if girl_name else 'du velger navnet på jenta'}
- De kommer fra {'samfunnslaget ' + samfunnslag if samfunnslag else 'et samfunnslag som du velger basert på tid og sted'}
- {'De har etnisk bakgrunn fra ' + etnisitet if etnisitet else 'Du velger etnisitet basert på sted og tid'}

Ungdommene hilser eleven vennlig og snakker i jeg-form direkte til dem. De deler hvordan livet deres er i dette samfunnet og forteller om hverdag, drømmer, utfordringer og håp.
Historien skal inneholde refleksjoner om skole, arbeid, familie og samfunnet rundt dem. Hvis historiske hendelser finner sted på denne tiden, må det gjerne nevnes.
Stilen skal være realistisk, ungdommelig og tilpasset videregående skole-elever.
Avslutt med at ungdommene sender en personlig hilsen til eleven og hele Øksnevad videregående skole.
Legg også til et visdomsord eller en inspirerende livsfilosofi som de gir med på veien – det kan være et sitat, eller noe de selv har funnet på, men det skal være meningsfullt for en elev i dag.
Til slutt spør de om eleven har noen spørsmål de lurer på om deres tid.
"""

                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du er en historieforteller. Historien blir fortalt i jeg-form av ungdommene selv som et kjærestepar i det historiske miljøet de lever i. De hilser på eleven som har reist i tid og avslutter med en personlig hilsen og visdomsord til Øksnevad vgs. Til slutt spør de eleven om det er noe de lurer på om deres tid."},
                        {"role": "user", "content": story_prompt}
                    ],
                    max_tokens=3000
                )

                story = response.choices[0].message.content
                st.session_state.story_data = {
                    "location": location,
                    "date": date,
                    "story": story,
                    "followups": [],
                    "samfunnslag": samfunnslag,
                    "etnisitet": etnisitet
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
    stil = "realistic, cinematic lighting, emotional, historically accurate clothing"
    if year < 1920:
        stil += ", sepia tone, Edwardian style"
    elif year < 1950:
        stil += ", 1940s fashion, monochrome photo style"
    elif year < 1980:
        stil += ", 1970s clothing, vintage tone"
    elif year < 2000:
        stil += ", 1990s youth fashion"
    if samfunnslag:
        stil += f", visual cues of {samfunnslag} background"
    etnisitet_prompt = f"{etnisitet} " if etnisitet else ""
    prompt = f"A {etnisitet_prompt}teenage couple (boy and girl, 16–18 years old) in love in {location} on {date}, {stil}"
    return prompt

# 📚 Vis historie og spørsmål
if st.session_state.get("historie_generert"):
    data = st.session_state.story_data
    st.markdown("### \U0001F4DD Her er historien:")
    st.markdown(data["story"])

    followup = st.text_input("Skriv et oppfølgingsspørsmål eller la stå tomt for å avslutte:", key="nytt_spm")
    if followup:
        if st.button("Still oppfølgingsspørsmål"):
            with st.spinner("De svarer..."):
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du svarer som ungdommene som akkurat har snakket med eleven fra Øksnevad. Svaret skal være i jeg-form og ungdommelig stil."},
                        {"role": "user", "content": f"Eleven spør: {followup}"}
                    ]
                )
                svar = response.choices[0].message.content
                data["followups"].append((followup, svar))
                st.rerun()

    for i, (spm, svar) in enumerate(data["followups"], start=1):
        st.markdown(f"### ❓ Spørsmål {i}:\n**{spm}**")
        st.markdown(f"### 💬 Svar:\n{svar}")

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

    full_story = data["story"] + "\n\n" + "\n".join([f"Spørsmål {i}: {q}\nSvar: {a}" for i, (q, a) in enumerate(data["followups"], start=1)])
    pdf_fil = lag_pdf(f"Historien fra {data['location']} den {data['date']}", full_story, data.get("bilde_path"))
    with open(pdf_fil, "rb") as f:
        st.download_button(
            label="\U0001F4C4 Last ned historien som PDF (med bilde)",
            data=f,
            file_name=f"historie_{data['location']}_{data['date']}.pdf",
            mime="application/pdf"
        )
