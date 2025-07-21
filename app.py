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
st.title("📖 Historiefortelleren – med Mark Twain som guide")

# 🧾 Brukerinput
year = st.text_input("Skriv inn årstall", placeholder="f.eks. 1917")
location = st.text_input("Skriv inn sted/land", placeholder="f.eks. Petrograd, Russland")
boy_name = st.text_input("Navn på gutten (valgfritt)")
girl_name = st.text_input("Navn på jenta (valgfritt)")

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
if st.button("Fortell meg en historie"):
    if not year or not location:
        st.warning("Skriv inn både årstall og sted for å komme i gang.")
    else:
        with st.spinner("Mark Twain setter seg godt til rette og begynner å fortelle..."):

            # 🎩 Prompt i Mark Twain-stil
            twain_prompt = f"""
Du er Mark Twain – eller en AI med samme skarpe penn, lune humor og evne til å fortelle historier om vanlige mennesker i uvanlige tider.

Skriv en varm, vittig, menneskelig og historisk troverdig novelle som foregår i {location} i året {year}. Historien skal handle om en gutt og en jente ({'gutten heter ' + boy_name if boy_name else 'du velger navnet på gutten'} og {'jenta heter ' + girl_name if girl_name else 'du velger navnet på jenta'}), og deres familier.

Historien skal:
- Ha en personlig og fortellende stil, som om du snakker til leseren
- Ha glimt i øyet og et snev av ironisk observasjon
- Være historisk troverdig ut fra sted og tid
- Være reflektert, men aldri moraliserende
- Inneholde menneskelig varme, klokhet og kanskje et lurt spark mot autoriteter

Du kan bruke en fortellerstemme i jeg-form, eller tredje person – men alltid med Mark Twains personlighet.

Avslutt gjerne med en liten kommentar, som bare en eldre, klok og litt rampete historieforteller kunne ha gitt.

Tittel på historien:  
"Hva som kunne skjedd i {location}, {year}"
"""

            # 📖 Hent fra GPT-4o
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du er Mark Twain – en skarp, vittig og menneskelig historieforteller som kjenner både historien og hjertene til folk."},
                    {"role": "user", "content": twain_prompt}
                ],
                max_tokens=3000
            )

            story = response["choices"][0]["message"]["content"]
            st.markdown("### 📝 Her er historien:")
            st.markdown(story)

            # 🖼️ DALL·E-bilde
            image_prompt = f"A boy and a girl in {location} in the year {year}, realistic historical scene, soft natural light, emotional, cinematic"
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

            # 💾 Lag PDF med bilde
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