import html
import io
import os

import pytesseract
import streamlit as st
from deep_translator import GoogleTranslator
from pdf2image import convert_from_bytes
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# -------------------------------------------------
# LOCAL PATH CONFIGURATION
# -------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

# Use Windows Tesseract path only when it exists.
# On Streamlit Cloud/Linux, the system-installed Tesseract is used.
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# -------------------------------------------------
# STREAMLIT PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Universal AI Translator",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Universal AI Translator")

st.write(
    "Upload an image or PDF, extract text using OCR, "
    "translate it into another language, and download the result."
)

# -------------------------------------------------
# DETECT INSTALLED OCR LANGUAGES
# -------------------------------------------------

@st.cache_data
def get_ocr_languages():
    try:
        languages = pytesseract.get_languages(config="")
        return sorted(languages)
    except Exception:
        return ["eng"]

LANGUAGE_NAMES = {
    "eng": "English",
    "tam": "Tamil",
    "hin": "Hindi",
    "tel": "Telugu",
    "mal": "Malayalam",
    "kan": "Kannada",
    "ben": "Bengali",
    "guj": "Gujarati",
    "mar": "Marathi",
    "urd": "Urdu",
    "ara": "Arabic",
    "fra": "French",
    "deu": "German",
    "spa": "Spanish",
    "ita": "Italian",
    "por": "Portuguese",
    "rus": "Russian",
    "chi_sim": "Chinese Simplified",
    "chi_tra": "Chinese Traditional",
    "jpn": "Japanese",
    "kor": "Korean",
}

def language_label(code):
    return f"{LANGUAGE_NAMES.get(code, code)} ({code})"

# -------------------------------------------------
# ALL TRANSLATION LANGUAGES
# -------------------------------------------------

TRANSLATION_LANGUAGES = {
    "Afrikaans": "af",
    "Albanian": "sq",
    "Amharic": "am",
    "Arabic": "ar",
    "Armenian": "hy",
    "Assamese": "as",
    "Aymara": "ay",
    "Azerbaijani": "az",
    "Bambara": "bm",
    "Basque": "eu",
    "Belarusian": "be",
    "Bengali": "bn",
    "Bhojpuri": "bho",
    "Bosnian": "bs",
    "Bulgarian": "bg",
    "Catalan": "ca",
    "Cebuano": "ceb",
    "Chinese Simplified": "zh-CN",
    "Chinese Traditional": "zh-TW",
    "Corsican": "co",
    "Croatian": "hr",
    "Czech": "cs",
    "Danish": "da",
    "Dhivehi": "dv",
    "Dogri": "doi",
    "Dutch": "nl",
    "English": "en",
    "Esperanto": "eo",
    "Estonian": "et",
    "Ewe": "ee",
    "Filipino": "tl",
    "Finnish": "fi",
    "French": "fr",
    "Frisian": "fy",
    "Galician": "gl",
    "Georgian": "ka",
    "German": "de",
    "Greek": "el",
    "Guarani": "gn",
    "Gujarati": "gu",
    "Haitian Creole": "ht",
    "Hausa": "ha",
    "Hawaiian": "haw",
    "Hebrew": "iw",
    "Hindi": "hi",
    "Hmong": "hmn",
    "Hungarian": "hu",
    "Icelandic": "is",
    "Igbo": "ig",
    "Ilocano": "ilo",
    "Indonesian": "id",
    "Irish": "ga",
    "Italian": "it",
    "Japanese": "ja",
    "Javanese": "jv",
    "Kannada": "kn",
    "Kazakh": "kk",
    "Khmer": "km",
    "Kinyarwanda": "rw",
    "Konkani": "gom",
    "Korean": "ko",
    "Krio": "kri",
    "Kurdish": "ku",
    "Kurdish Sorani": "ckb",
    "Kyrgyz": "ky",
    "Lao": "lo",
    "Latin": "la",
    "Latvian": "lv",
    "Lingala": "ln",
    "Lithuanian": "lt",
    "Luganda": "lg",
    "Luxembourgish": "lb",
    "Macedonian": "mk",
    "Maithili": "mai",
    "Malagasy": "mg",
    "Malay": "ms",
    "Malayalam": "ml",
    "Maltese": "mt",
    "Maori": "mi",
    "Marathi": "mr",
    "Meiteilon": "mni-Mtei",
    "Mizo": "lus",
    "Mongolian": "mn",
    "Myanmar": "my",
    "Nepali": "ne",
    "Norwegian": "no",
    "Nyanja": "ny",
    "Odia": "or",
    "Oromo": "om",
    "Pashto": "ps",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Quechua": "qu",
    "Romanian": "ro",
    "Russian": "ru",
    "Samoan": "sm",
    "Sanskrit": "sa",
    "Scots Gaelic": "gd",
    "Sepedi": "nso",
    "Serbian": "sr",
    "Sesotho": "st",
    "Shona": "sn",
    "Sindhi": "sd",
    "Sinhala": "si",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Somali": "so",
    "Spanish": "es",
    "Sundanese": "su",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tajik": "tg",
    "Tamil": "ta",
    "Tatar": "tt",
    "Telugu": "te",
    "Thai": "th",
    "Tigrinya": "ti",
    "Tsonga": "ts",
    "Turkish": "tr",
    "Turkmen": "tk",
    "Twi": "ak",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Uyghur": "ug",
    "Uzbek": "uz",
    "Vietnamese": "vi",
    "Welsh": "cy",
    "Xhosa": "xh",
    "Yiddish": "yi",
    "Yoruba": "yo",
    "Zulu": "zu",
}

# -------------------------------------------------
# TRANSLATION FUNCTION
# -------------------------------------------------

def safe_translate(text, target_lang, max_chars=4500):
    if not text or not text.strip():
        return "No text detected."

    chunks = [
        text[i:i + max_chars]
        for i in range(0, len(text), max_chars)
    ]

    translated_chunks = []

    for chunk in chunks:
        translated = GoogleTranslator(
            source="auto",
            target=target_lang
        ).translate(chunk)

        translated_chunks.append(translated)

    return "\n".join(translated_chunks)

# -------------------------------------------------
# PDF FONT SUPPORT
# -------------------------------------------------

def get_pdf_font(target_lang):
    font_name = "Helvetica"

    if target_lang in ["zh-CN", "zh-TW"]:
        font_name = "STSong-Light"
    elif target_lang == "ja":
        font_name = "HeiseiMin-W3"
    elif target_lang == "ko":
        font_name = "HYSMyeongJo-Medium"

    if font_name != "Helvetica":
        try:
            pdfmetrics.registerFont(
                UnicodeCIDFont(font_name)
            )
        except Exception:
            font_name = "Helvetica"

    return font_name

# -------------------------------------------------
# CREATE TRANSLATED PDF
# -------------------------------------------------

def create_pdf(translated_pages, target_lang):
    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4
    )

    font_name = get_pdf_font(target_lang)

    styles = getSampleStyleSheet()
    style = styles["Normal"]

    style.fontName = font_name
    style.leading = 20

    story = []

    for page_number, text in enumerate(
        translated_pages,
        start=1
    ):
        story.append(
            Paragraph(
                f"<b>Page {page_number}</b>",
                style
            )
        )

        story.append(
            Spacer(1, 15)
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

# -------------------------------------------------
# OCR LANGUAGE SELECTION
# -------------------------------------------------

installed_languages = [
    language
    for language in get_ocr_languages()
    if language != "osd"
]

if not installed_languages:
    st.error("No OCR languages were detected.")
    st.stop()

default_index = 0

if "eng" in installed_languages:
    default_index = installed_languages.index("eng")

st.subheader("1️⃣ Select Input Document Language")

ocr_language = st.selectbox(
    "Language in your Image or PDF",
    installed_languages,
    index=default_index,
    format_func=language_label
)

# -------------------------------------------------
# TARGET TRANSLATION LANGUAGE
# -------------------------------------------------

st.subheader("2️⃣ Select Translation Language")

target_language_name = st.selectbox(
    "Translate To",
    sorted(TRANSLATION_LANGUAGES.keys())
)

target_language = TRANSLATION_LANGUAGES[
    target_language_name
]

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------

st.subheader("3️⃣ Upload Image or PDF")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["png", "jpg", "jpeg", "pdf"]
)

# -------------------------------------------------
# PROCESS FILE
# -------------------------------------------------

if uploaded_file is not None:
    try:
        with st.spinner(
            "Reading and translating your document..."
        ):
            file_bytes = uploaded_file.getvalue()

            is_image = "image" in uploaded_file.type

            if is_image:
                input_images = [
                    Image.open(
                        io.BytesIO(file_bytes)
                    )
                ]
            else:
                poppler_kwargs = {}

                if os.path.exists(POPPLER_PATH):
                    poppler_kwargs["poppler_path"] = POPPLER_PATH

                input_images = convert_from_bytes(
                    file_bytes,
                    **poppler_kwargs
                )

            translated_pages = []
            preview_data = []

            progress_bar = st.progress(0)
            total_pages = len(input_images)

            for index, image in enumerate(input_images):
                raw_text = pytesseract.image_to_string(
                    image,
                    lang=ocr_language
                )

                translated_text = safe_translate(
                    raw_text,
                    target_language
                )

                translated_pages.append(translated_text)

                preview_data.append(
                    (
                        raw_text,
                        translated_text
                    )
                )

                percentage = int(
                    ((index + 1) / total_pages) * 100
                )

                progress_bar.progress(percentage)

            progress_bar.empty()

        st.success("✅ Translation completed successfully!")

        # -----------------------------------------
        # DISPLAY RESULTS
        # -----------------------------------------

        for page_number, data in enumerate(
            preview_data,
            start=1
        ):
            raw_text = data[0]
            translated_text = data[1]

            st.subheader(f"📄 Page {page_number}")

            column1, column2 = st.columns(2)

            with column1:
                st.caption("Original Extracted Text")
                st.text_area(
                    "OCR Text",
                    value=raw_text,
                    height=300,
                    key=f"original_{page_number}"
                )

            with column2:
                st.caption("Translated Text")
                st.text_area(
                    "Translation",
                    value=translated_text,
                    height=300,
                    key=f"translated_{page_number}"
                )

        # -----------------------------------------
        # DOWNLOAD TRANSLATED TEXT
        # -----------------------------------------

        complete_text = "\n\n".join(
            f"--- Page {index + 1} ---\n{text}"
            for index, text in enumerate(translated_pages)
        )

        st.download_button(
            "📥 Download Translated Text",
            data=complete_text.encode("utf-8"),
            file_name="translated.txt",
            mime="text/plain"
        )

        # -----------------------------------------
        # DOWNLOAD TRANSLATED PDF
        # -----------------------------------------

        try:
            pdf_data = create_pdf(
                translated_pages,
                target_language
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
                "failed for this target language."
            )
            st.code(str(pdf_error))

    except Exception as error:
        st.error(
            "❌ Something went wrong while processing the file."
        )
        st.exception(error)
