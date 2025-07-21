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

# 🔐 Hent API-nøkkel fra Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🎨 Streamlit-oppsett
st.set_page_config(page_title="Historiefortelleren", page_icon="📖")
st.title("📖 Historiefortelleren – reis i tid med AI")

# 📜 Brukerinput
year = st.text_input("Skriv inn årstall", placeholder="f.eks. 1917")
location = st.text_input("Skriv inn sted/land", placeholder="f.eks. Petrograd, Russland")
boy_name = st.text_input("Navn på gutten (valgfritt)")
girl_name = st.text_input("Navn på jenta (valgfritt)")

# 📋 PDF-funksjon
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
if st.button("Fortell meg en historie"):
    if not year or not location:
        st.warning("Skriv inn både årstall og sted for å komme i gang.")
    else:
        with st.spinner("Reiser tilbake i tid..."):
            story_prompt = f"""
Du skal skrive en realistisk og varm historie satt til {location} i året {year}. Historien skal handle om en gutt og en jente ({'gutten heter ' + boy_name if boy_name else 'du velger navnet på gutten'} og {'jenta heter ' + girl_name if girl_name else 'du velger navnet på jenta'}), og deres familier.

Historien skal være realistisk basert på tidsepoken, men fokusere på menneskelighet, håp og relasjoner. Dersom det er vanskelige historiske omstendigheter, nevnes det, men tonen skal være livsnær og ikke dyster.

Fortell det som en mini-novelle med tydelige beskrivelser og følelser. Avslutt gjerne med en liten refleksjon.
            """

            chat_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du er Mark Twain, en historieforteller med kunnskap om verdenshistorien og menneskelig empati."},
                    {"role": "user", "content": story_prompt}
                ],
                max_tokens=3000
            )

            story = chat_response.choices[0].message.content
            st.markdown("### 📝 Her er historien:")
            st.markdown(story)

            # 🖼️ Bilde fra DALL-E 3
            image_prompt = f"A boy and a girl in {location} in the year {year}, realistic historical scene, soft natural light, emotional, cinematic"
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )

            image_url = image_response.data[0].url
            image = Image.open(BytesIO(requests.get(image_url).content))

            st.markdown("### 🖼️ Historisk illustrasjon:")
            st.image(image, caption=f"{location}, {year}")

            temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_image_file.name)

            pdf_fil = lag_pdf(f"Historien fra {location} i {year}", story, temp_image_file.name)

            with open(pdf_fil, "rb") as f:
                st.download_button(
                    label="📄 Last ned historien som PDF (med bilde)",
                    data=f,
                    file_name=f"historie_{location}_{year}.pdf",
                    mime="application/pdf"
                )