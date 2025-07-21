import streamlit as st
import os
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# 🔐 OpenAI API-nøkkel fra secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🎨 Streamlit-oppsett
st.set_page_config(page_title="Historiefortelleren", page_icon="📖")
st.title("📖 Historiefortelleren – en reise tilbake i tid")

# 🧾 Brukerinput
year = st.text_input("Skriv inn årstall", placeholder="f.eks. 1917")
location = st.text_input("Skriv inn sted/land", placeholder="f.eks. Petrograd, Russland")

# 📄 PDF-funksjon
def lag_pdf(tittel, tekst, bilde_path=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)

    # Tittel
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, 28 * cm, tittel)

    y = 27 * cm

    # Bilde
    if bilde_path:
        try:
            c.drawImage(bilde_path, 2 * cm, y - 12 * cm, width=12 * cm, height=12 * cm, preserveAspectRatio=True)
            y -= 13 * cm
        except Exception as e:
            print("Kunne ikke legge til bilde i PDF:", e)

    # Tekst
    c.setFont("Helvetica", 12)
    for linje in tekst.split("\n"):
        if y < 2 * cm:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 27 * cm
        c.drawString(2 * cm, y, linje[:100])
        y -= 0.6 * cm

    c.save()
    return temp_file.name

# 🚀 Generer historie
if st.button("Start tidsreisen!"):
    if not year or not location:
        st.warning("Skriv inn både årstall og sted for å komme i gang.")
    else:
        with st.spinner("Reiser tilbake i tid..."):

            # 🧠 Prompt
            prompt = f"""
Forestill deg at eleven har gått inn i en tidsmaskin og havner i {location} i året {year}. Når de kommer frem, møter de en gutt og en jente på 16–18 år.

De to ungdommene forteller hvordan livet deres er som unge i denne tiden og på dette stedet. De snakker om hverdagen, utfordringer, håp og drømmer – og kanskje også om historiske hendelser som påvirker dem.

Svarene skal være tilpasset dagens ungdom på Øksnevad vgs – altså realistisk, relaterbart og med en ungdommelig fortellerstil. Ikke gjør det for gammeldags. Språket skal være ungdommelig, lett å lese, og gjerne litt personlig og sårbart der det passer.

Fortellingen skal fenge og gi innsikt i historiske forhold – gjennom øynene til ungdom som levde da.
"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du er en ungdom som lever i fortiden og forteller om hvordan det er å være ung i din tid."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000
            )

            story = response.choices[0].message.content
            st.markdown("### 📝 Dette fortalte ungdommene:")
            st.markdown(story)

            # 🖼️ DALL·E-bilde
            image_prompt = f"A boy and a girl aged 16–18 in {location} in the year {year}, historical scene, cinematic, emotional, realistic"
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )
            image_url = image_response.data[0].url
            image = Image.open(BytesIO(requests.get(image_url).content))

            st.markdown("### 🖼️ Tidsbilde:")
            st.image(image, caption=f"{location}, {year}")

            # 💾 Lag PDF med bilde
            temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_image_file.name)

            pdf_fil = lag_pdf(f"Reise til {location} i {year}", story, temp_image_file.name)

            with open(pdf_fil, "rb") as f:
                st.download_button(
                    label="📄 Last ned historien som PDF (med bilde)",
                    data=f,
                    file_name=f"tidsreise_{location}_{year}.pdf",
                    mime="application/pdf"
                )