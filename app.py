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
st.title("📖 Historiefortelleren – Tidsreise med ungdom i fokus")

# 📅 Brukerinput
year = st.text_input("Skriv inn et årstall du vil reise til", placeholder="f.eks. 1944")
location = st.text_input("Skriv inn et sted/land", placeholder="f.eks. Normandie, Frankrike")

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
        st.warning("Du må skrive inn både årstall og sted.")
    else:
        with st.spinner("Skrur på tidsmaskinen..."):
            story_prompt = f"""
Du er en AI-forteller som lager en levende fortelling for en norsk ungdom (16–19 år) på videregående.

Eleven har valgt å reise tilbake til {location} i året {year}.

Skriv en historie der eleven møter to ungdommer (en gutt og en jente på ca. 16–18 år). Historien fortelles av ungdommene selv, i førsteperson. De beskriver:

- Hvem de er
- Hvordan livet deres er som ungdom
- Hvordan samfunnet rundt dem er
- Hva de drømmer om og hva de frykter
- Hvilke historiske hendelser de merker noe til (om relevant)

Tonen skal være personlig, varm og naturlig, skrevet slik ungdom på vgs i Norge forstår og kan leve seg inn i. Gjør det ekte og engasjerende.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du er en empatisk ungdom med kunnskap om historien og evne til å fortelle levende historier fra ulike tider."},
                    {"role": "user", "content": story_prompt}
                ],
                max_tokens=3000
            )

            story = response["choices"][0]["message"]["content"]
            st.markdown("### 🖋️ Historien:")
            st.markdown(story)

            image_prompt = f"Two teenagers (a boy and a girl) in {location} in the year {year}, realistic historical setting, cinematic lighting"
            image_response = openai.Image.create(
                model="dall-e-3",
                prompt=image_prompt,
                n=1,
                size="1024x1024"
            )
            image_url = image_response['data'][0]['url']
            image = Image.open(BytesIO(requests.get(image_url).content))

            st.markdown("### 🖼️ Historisk illustrasjon:")
            st.image(image, caption=f"{location}, {year}")

            temp_image_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_image_file.name)

            pdf_fil = lag_pdf(f"Historien fra {location}, {year}", story, temp_image_file.name)

            with open(pdf_fil, "rb") as f:
                st.download_button(
                    label="📄 Last ned som PDF",
                    data=f,
                    file_name=f"historie_{location}_{year}.pdf",
                    mime="application/pdf"
                )