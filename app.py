import streamlit as st
from PIL import Image
import pytesseract
from deep_translator import GoogleTranslator
from pdf2image import convert_from_bytes
import io
import html
import os

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4

-------------------------------------------------
WINDOWS / LOCAL CONFIGURATION
-------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

Configure Tesseract only when the Windows path exists

if os.path.exists(TESSERACT_PATH):
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

-------------------------------------------------
STREAMLIT PAGE
-------------------------------------------------

st.set_page_config(
page_title="Universal AI Translator",
page_icon="🌍",
layout="wide"
)

st.title("🌍 Universal OCR & Multi-Language Translator")

st.write(
"Upload an image or PDF, extract text using OCR, "
"translate it into another language, and download the result."
)

-------------------------------------------------
DETECT OCR LANGUAGES
-------------------------------------------------

@st.cache_data
def get_installed_ocr_languages():
try:
return sorted(pytesseract.get_languages(config=""))
except Exception:
return ["eng"]

LANGUAGE_NAMES = {
"eng": "English",
"tam": "Tamil",
"hin": "Hindi",
"ara": "Arabic",
"chi_sim": "Chinese Simplified",
"chi_tra": "Chinese Traditional",
"jpn": "Japanese",
"kor": "Korean",
"fra": "French",
"deu": "German",
"spa": "Spanish",
"ita": "Italian",
"por": "Portuguese",
"rus": "Russian",
"ben": "Bengali",
"tel": "Telugu",
"kan": "Kannada",
"mal": "Malayalam",
"mar": "Marathi",
"guj": "Gujarati",
"urd": "Urdu"
}

def language_label(code):
return f"{LANGUAGE_NAMES.get(code, code)} ({code})"

-------------------------------------------------
TRANSLATION LANGUAGES
-------------------------------------------------

available_langs = {
"Afrikaans": "af",
"Arabic": "ar",
"Bengali": "bn",
"Chinese Simplified": "zh-CN",
"Chinese Traditional": "zh-TW",
"Dutch": "nl",
"English": "en",
"French": "fr",
"German": "de",
"Greek": "el",
"Gujarati": "gu",
"Hindi": "hi",
"Indonesian": "id",
"Italian": "it",
"Japanese": "ja",
"Kannada": "kn",
"Korean": "ko",
"Malayalam": "ml",
"Marathi": "mr",
"Polish": "pl",
"Portuguese": "pt",
"Punjabi": "pa",
"Russian": "ru",
"Spanish": "es",
"Tamil": "ta",
"Telugu": "te",
"Thai": "th",
"Turkish": "tr",
"Ukrainian": "uk",
"Urdu": "ur",
"Vietnamese": "vi"
}

-------------------------------------------------
PDF FONT
-------------------------------------------------

def get_pdf_font(lang_code):
font_name = "Helvetica"

if lang_code in ["zh-CN", "zh-TW"]:
    font_name = "STSong-Light"

elif lang_code == "ja":
    font_name = "HeiseiMin-W3"

elif lang_code == "ko":
    font_name = "HYSMyeongJo-Medium"

if font_name != "Helvetica":
    try:
        pdfmetrics.registerFont(
            UnicodeCIDFont(font_name)
        )
    except Exception:
        pass

return font_name
-------------------------------------------------
CREATE PDF
-------------------------------------------------

def make_pdf(translated_pages, font_name):
output = io.BytesIO()

document = SimpleDocTemplate(
    output,
    pagesize=A4
)

styles = getSampleStyleSheet()
style = styles["Normal"]

style.fontName = font_name
style.leading = 22

story = []

for page_number, text in enumerate(translated_pages, start=1):
    story.append(
        Paragraph(
            f"Page {page_number}",
            style
        )
    )

    story.append(Spacer(1, 12))

    paragraphs = html.escape(text).split("\n")

    for paragraph in paragraphs:
        if paragraph.strip():
            story.append(
                Paragraph(
                    paragraph,
                    style
                )
            )

            story.append(
                Spacer(1, 8)
            )

    story.append(
        Spacer(1, 20)
    )

document.build(story)

return output.getvalue()
-------------------------------------------------
OCR LANGUAGE SELECTION
-------------------------------------------------

installed_ocr_languages = get_installed_ocr_languages()

if not installed_ocr_languages:
st.error("No Tesseract OCR languages were detected.")
st.stop()

if "eng" in installed_ocr_languages:
default_index = installed_ocr_languages.index("eng")
else:
default_index = 0

st.subheader("1️⃣ Select Input Document Language")

ocr_lang = st.selectbox(
"Language of the uploaded document",
installed_ocr_languages,
index=default_index,
format_func=language_label
)

-------------------------------------------------
TARGET LANGUAGE
-------------------------------------------------

st.subheader("2️⃣ Select Translation Language")

target_lang_name = st.selectbox(
"Translate to",
sorted(available_langs.keys())
)

target_code = available_langs[target_lang_name]

-------------------------------------------------
FILE UPLOAD
-------------------------------------------------

st.subheader("3️⃣ Upload File")

uploaded_file = st.file_uploader(
"Upload Image or PDF",
type=["png", "jpg", "jpeg", "pdf"]
)

-------------------------------------------------
PROCESS FILE
-------------------------------------------------

if uploaded_file is not None:

try:

    with st.spinner("Reading and translating your file..."):

        # Check whether the uploaded file is an image
        if "image" in uploaded_file.type:
            input_images = [
                Image.open(uploaded_file)
            ]

        # Otherwise, process it as a PDF
        else:
            pdf_kwargs = {}

            if os.path.exists(POPPLER_PATH):
                pdf_kwargs["poppler_path"] = POPPLER_PATH

            input_images = convert_from_bytes(
                uploaded_file.read(),
                **pdf_kwargs
            )

        translated_pages = []
        previews = []

        progress_bar = st.progress(0)

        for index, image in enumerate(input_images):

            # OCR
            raw_text = pytesseract.image_to_string(
                image,
                lang=ocr_lang
            )

            # Translation
            if raw_text.strip():

                translated_text = GoogleTranslator(
                    source="auto",
                    target=target_code
                ).translate(raw_text)

            else:
                translated_text = "No text detected."

            translated_pages.append(
                translated_text
            )

            previews.append(
                (
                    raw_text,
                    translated_text
                )
            )

            progress = int(
                ((index + 1) / len(input_images)) * 100
            )

            progress_bar.progress(progress)

        progress_bar.empty()

        st.success("✅ Translation completed successfully!")

        # -----------------------------------------
        # SHOW RESULTS
        # -----------------------------------------

        for page_number, (
            raw_text,
            translated_text
        ) in enumerate(previews, start=1):

            st.subheader(f"📄 Page {page_number}")

            col1, col2 = st.columns(2)

            with col1:

                st.caption("Extracted OCR Text")

                st.text_area(
                    "OCR Result",
                    raw_text,
                    height=300,
                    key=f"ocr_{page_number}"
                )

            with col2:

                st.caption("Translated Text")

                st.text_area(
                    "Translation Result",
                    translated_text,
                    height=300,
                    key=f"translation_{page_number}"
                )

        # -----------------------------------------
        # TEXT DOWNLOAD
        # -----------------------------------------

        all_text = "\n\n".join(
            f"--- Page {i + 1} ---\n{text}"
            for i, text in enumerate(translated_pages)
        )

        st.download_button(
            "📥 Download Translated Text",
            data=all_text.encode("utf-8"),
            file_name="translated.txt",
            mime="text/plain"
        )

        # -----------------------------------------
        # PDF DOWNLOAD
        # -----------------------------------------

        try:

            pdf_font = get_pdf_font(target_code)

            pdf_data = make_pdf(
                translated_pages,
                pdf_font
            )

            st.download_button(
                "📄 Download Translated PDF",
                data=pdf_data,
                file_name="translated.pdf",
                mime="application/pdf"
            )

        except Exception as pdf_error:

            st.warning(
                "Translation succeeded, but PDF generation "
                "failed for this language."
            )

            st.code(str(pdf_error))

except Exception as error:

    st.error(
        "❌ An error occurred while processing the file."
    )

    st.exception(error)
