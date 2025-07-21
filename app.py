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
st.set_page_config(page_title="Historiefortelleren", page_icon="📖")
st.title("📖 Historiefortelleren – reis i tid med AI")

# 🧾 Brukerinput
date = st.text_input("Skriv inn dato (DD.MM.ÅÅÅÅ)", placeholder="f.eks. 01.05.1945")
location = st.text_input("Skriv inn sted/land", placeholder="f.eks. Berlin, Tyskland")
boy_name = st.text_input("Navn på gutten (valgfritt)")
girl_name = st.text_input("Navn på jenta (valgfritt)")

# 📄 PDF-funksjon
def lag_pdf(tittel, tekst, bilde_path=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, 28 * cm, tittel)

    y = 27 * cm

    if bilde_path:
        try:
            c.drawImage(bilde_path, 2 * cm, y - 12 * cm, width=12 * cm, height=12 * cm, preserveAspectRatio=True)
            y -= 13 * cm
        except Exception as e:
            print("Kunne ikke legge til bilde i PDF:", e)

    c.setFont("Helvetica", 12)
    for linje i tekst.split("\n"):
        if y < 2 * cm:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 27 * cm
        c.drawString(2 * cm, y, linje[:100])
        y -= 0.6 * cm

    c.save()
    return temp_file.name

# 🎯 Generer bildeprompt basert på dato og sted
def generer_bildeprompt(location, date):
    try:
        year = int(date.split(".")[-1])
    except:
        year = 1950

    nasjonalitet = "European"
    stil = "realistic, cinematic lighting, emotional, historically accurate clothing"

    loc_lower = location.lower()
    if "germany" in loc_lower or "berlin" in loc_lower:
        nasjonalitet = "German"
    elif "norway" in loc_lower or "oslo" in loc_lower:
        nasjonalitet = "Norwegian"
    elif "france" in loc_lower or "paris" in loc_lower:
        nasjonalitet = "French"
    elif "usa" in loc_lower or "america" in loc_lower or "new york" in loc_lower:
        nasjonalitet = "American"
    elif "russia" in loc_lower or "moscow" in loc_lower or "soviet" in loc_lower:
        nasjonalitet = "Russian"

    if year < 1920:
        stil += ", sepia tone, Edwardian style"
    elif year < 1950:
        stil += ", 1940s fashion, monochrome photo style"
    elif year < 1980:
        stil += ", 1970s clothing, vintage tone"
    elif year < 2000:
        stil += ", 1990s youth fashion"

    prompt = f"A {nasjonalitet} teenage couple (boy and girl, 16–18 years old) in love in {location} on {date}, {stil}"
    return prompt

# 🚀 Generer historie
if st.button("Fortell meg en historie"):
    if not date or not location:
        st.warning("Skriv inn både dato og sted for å komme i gang.")
    else:
        with st.spinner("Reiser tilbake i tid..."):

            story_prompt = f"""
Skriv en realistisk og engasjerende historie satt til {location} den {date}.

Når eleven ankommer som en tidsreisende, møter de to ungdommer (ca. 16–18 år) som er kjærester:
- {'gutten heter ' + boy_name if boy_name else 'du velger navnet på gutten'}
- {'jenta heter ' + girl_name if girl_name else 'du velger navnet på jenta'}

Ungdommene forteller hvordan livet deres er i dette samfunnet, og deler tanker, drømmer og håp som kjærestepar.
De reflekterer over skole, arbeid, familie, og samfunnet rundt seg. Hvis historiske hendelser finner sted på denne tiden, må det gjerne nevnes.
Historien skal passe for ungdom på videregående skole og være troverdig.
"""

            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du er en historieforteller. Historien blir fortalt av ungdommene selv som et kjærestepar i det historiske miljøet de lever i."},
                    {"role": "user", "content": story_prompt}
                ],
                max_tokens=3000
            )

            story = response.choices[0].message.content
            st.markdown("### 📝 Her er historien:")
            st.markdown(story)

            image_prompt = generer_bildeprompt(location, date)

            image_response = openai.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )
            image_url = image_response.data[0].url
            image = Image.open(BytesIO(requests.get(image_url).content))

            st.markdown("### 🖼️ Historisk illustrasjon:")
            st.image(image, caption=f"{location}, {date}")

            temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_image_file.name)

            pdf_fil = lag_pdf(f"Historien fra {location} den {date}", story, temp_image_file.name)

            with open(pdf_fil, "rb") as f:
                st.download_button(
                    label="📄 Last ned historien som PDF (med bilde)",
                    data=f,
                    file_name=f"historie_{location}_{date}.pdf",
                    mime="application/pdf"
                )