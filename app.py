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

# =========================================================

# WINDOWS / CLOUD CONFIGURATION

# =========================================================

# Windows paths for local use

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

# Configure Tesseract only when running on Windows

if os.path.exists(TESSERACT_PATH):
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# =========================================================

# STREAMLIT PAGE

# =========================================================

st.set_page_config(
page_title="Universal AI Translator",
page_icon="🌍",
layout="wide"
)

st.title("🌍 Universal OCR & Multi-Language Translator")

st.write(
"Upload an image or PDF, extract text using OCR, "
"translate it into multiple languages, and download the result."
)

# =========================================================

# DETECT INSTALLED TESSERACT OCR LANGUAGES

# =========================================================

@st.cache_data
def get_installed_ocr_languages():
try:
languages = pytesseract.get_languages(config="")
return sorted(languages)

```
except Exception:
    return ["eng"]
```

# Display names for common OCR languages

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
"urd": "Urdu",
"tha": "Thai",
"vie": "Vietnamese"
}

def language_label(code):
return f"{LANGUAGE_NAMES.get(code, code)} ({code})"

# =========================================================

# TRANSLATION LANGUAGES

# =========================================================

available_langs = {
"Afrikaans": "af",
"Albanian": "sq",
"Amharic": "am",
"Arabic": "ar",
"Armenian": "hy",
"Azerbaijani": "az",
"Basque": "eu",
"Belarusian": "be",
"Bengali": "bn",
"Bosnian": "bs",
"Bulgarian": "bg",
"Catalan": "ca",
"Chinese Simplified": "zh-CN",
"Chinese Traditional": "zh-TW",
"Croatian": "hr",
"Czech": "cs",
"Danish": "da",
"Dutch": "nl",
"English": "en",
"Esperanto": "eo",
"Estonian": "et",
"Finnish": "fi",
"French": "fr",
"Galician": "gl",
"Georgian": "ka",
"German": "de",
"Greek": "el",
"Gujarati": "gu",
"Haitian Creole": "ht",
"Hebrew": "iw",
"Hindi": "hi",
"Hungarian": "hu",
"Icelandic": "is",
"Indonesian": "id",
"Irish": "ga",
"Italian": "it",
"Japanese": "ja",
"Kannada": "kn",
"Kazakh": "kk",
"Korean": "ko",
"Latin": "la",
"Latvian": "lv",
"Lithuanian": "lt",
"Macedonian": "mk",
"Malay": "ms",
"Malayalam": "ml",
"Maltese": "mt",
"Marathi": "mr",
"Mongolian": "mn",
"Nepali": "ne",
"Norwegian": "no",
"Persian": "fa",
"Polish": "pl",
"Portuguese": "pt",
"Punjabi": "pa",
"Romanian": "ro",
"Russian": "ru",
"Serbian": "sr",
"Sinhala": "si",
"Slovak": "sk",
"Slovenian": "sl",
"Spanish": "es",
"Swahili": "sw",
"Swedish": "sv",
"Tamil": "ta",
"Telugu": "te",
"Thai": "th",
"Turkish": "tr",
"Ukrainian": "uk",
"Urdu": "ur",
"Uzbek": "uz",
"Vietnamese": "vi",
"Welsh": "cy"
}

# =========================================================

# PDF FONT SUPPORT

# =========================================================

def get_pdf_font(lang_code):

```
font_name = "Helvetica"

if lang_code in ["zh-CN", "zh-TW", "zh"]:
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
```

# =========================================================

# CREATE TRANSLATED PDF

# =========================================================

def make_pdf(translated_pages, font_name):

```
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

for page_number, text in enumerate(
    translated_pages,
    start=1
):

    story.append(
        Paragraph(
            f"Page {page_number}",
            style
        )
    )

    story.append(
        Spacer(1, 12)
    )

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
```

# =========================================================

# SELECT OCR LANGUAGE

# =========================================================

installed_ocr_languages = get_installed_ocr_languages()

if not installed_ocr_languages:

```
st.error(
    "No Tesseract OCR languages were detected."
)

st.stop()
```

if "eng" in installed_ocr_languages:

```
default_index = installed_ocr_languages.index("eng")
```

else:

```
default_index = 0
```

st.subheader("1️⃣ Select Input Document Language")

ocr_lang = st.selectbox(
"Language of the uploaded image or PDF",
installed_ocr_languages,
index=default_index,
format_func=language_label
)

# =========================================================

# SELECT TARGET LANGUAGE

# =========================================================

st.subheader("2️⃣ Select Translation Language")

target_lang_name = st.selectbox(
"Translate to",
sorted(available_langs.keys())
)

target_code = available_langs[target_lang_name]

# =========================================================

# UPLOAD FILE

# =========================================================

st.subheader("3️⃣ Upload Your File")

uploaded_file = st.file_uploader(
"Upload Image or PDF",
type=[
"png",
"jpg",
"jpeg",
"pdf"
]
)

# =========================================================

# PROCESS FILE

# =========================================================

if uploaded_file is not None:

```
try:

    with st.spinner(
        "Reading and translating your file..."
    ):

        # ---------------------------------------------
        # IMAGE INPUT
        # ---------------------------------------------

        if "image" in uploaded_file.type:

            input_images = [
                Image.open(uploaded_file)
            ]


        # ---------------------------------------------
        # PDF INPUT
        # ---------------------------------------------

        else:

            pdf_kwargs = {}

            # Use Poppler path only on Windows
            if os.path.exists(POPPLER_PATH):

                pdf_kwargs[
                    "poppler_path"
                ] = POPPLER_PATH


            input_images = convert_from_bytes(
                uploaded_file.read(),
                **pdf_kwargs
            )


        translated_pages = []

        previews = []

        progress_bar = st.progress(0)


        # ---------------------------------------------
        # OCR + TRANSLATION
        # ---------------------------------------------

        for index, image in enumerate(
            input_images
        ):

            # Extract text
            raw_text = (
                pytesseract.image_to_string(
                    image,
                    lang=ocr_lang
                )
            )


            # Translate text
            if raw_text.strip():

                translator = GoogleTranslator(
                    source="auto",
                    target=target_code
                )

                translated_text = translator.translate(
                    raw_text
                )

            else:

                translated_text = (
                    "No text detected."
                )


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
                (
                    (index + 1)
                    /
                    len(input_images)
                )
                * 100
            )

            progress_bar.progress(
                progress
            )


        progress_bar.empty()


        # =================================================
        # DISPLAY RESULTS
        # =================================================

        st.success(
            "✅ Translation completed successfully!"
        )


        for page_number, (
            raw_text,
            translated_text
        ) in enumerate(
            previews,
            start=1
        ):

            st.subheader(
                f"📄 Page {page_number}"
            )


            col1, col2 = st.columns(2)


            # OCR TEXT
            with col1:

                st.caption(
                    "Extracted OCR Text"
                )

                st.text_area(
                    "OCR Result",
                    raw_text,
                    height=300,
                    key=f"ocr_{page_number}"
                )


            # TRANSLATED TEXT
            with col2:

                st.caption(
                    "Translated Text"
                )

                st.text_area(
                    "Translation Result",
                    translated_text,
                    height=300,
                    key=f"translation_{page_number}"
                )


        # =================================================
        # DOWNLOAD TRANSLATED TEXT
        # =================================================

        all_text = "\n\n".join(

            f"--- Page {i + 1} ---\n{text}"

            for i, text in enumerate(
                translated_pages
            )

        )


        st.download_button(

            "📥 Download Translated Text",

            data=all_text.encode(
                "utf-8"
            ),

            file_name="translated.txt",

            mime="text/plain"

        )


        # =================================================
        # DOWNLOAD TRANSLATED PDF
        # =================================================

        try:

            pdf_font = get_pdf_font(
                target_code
            )

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
                "could not be completed for this language."
            )

            st.code(
                str(pdf_error)
            )


except Exception as error:

    st.error(
        "❌ An error occurred while processing the file."
    )

    st.exception(error)
```
