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
# LOCAL PATH CONFIGURATION (WINDOWS SAFEGUARD)
# -------------------------------------------------
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# -------------------------------------------------
# STREAMLIT PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Universal AI Translator", page_icon="🌍", layout="wide"
)

st.title("🌍 Universal AI Translator")
st.write(
    "Upload an image or PDF, extract text using OCR, "
    "translate it into another language, and download the result."
)


# -------------------------------------------------
# LANGUAGE CONFIGURATION
# -------------------------------------------------
@st.cache_data
def get_ocr_languages():
    try:
        return sorted(pytesseract.get_languages(config=""))
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


TRANSLATION_LANGUAGES = {
    "Afrikaans": "af",
    "Albanian": "sq",
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese Simplified": "zh-CN",
    "Chinese Traditional": "zh-TW",
    "Croatian": "hr",
    "Czech": "cs",
    "Danish": "da",
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
    "Norwegian": "no",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Romanian": "ro",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
}


# -------------------------------------------------
# TRANSLATION & PDF HELPERS
# -------------------------------------------------
def safe_translate(text, target_lang, max_chars=4500):
    """Splits long text blocks to prevent deep_translator length limit crashes."""
    if not text.strip():
        return "No text detected."

    chunks = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
    translated_chunks = []

    for chunk in chunks:
        translated = GoogleTranslator(
            source="auto", target=target_lang
        ).translate(chunk)
        translated_chunks.append(translated)

    return "".join(translated_chunks)


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
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))
        except Exception:
            font_name = "Helvetica"
    return font_name


def create_pdf(translated_pages, target_lang):
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4)

    font_name = get_pdf_font(target_lang)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = font_name
    style.leading = 20

    story = []

    for page_number, text in enumerate(translated_pages, start=1):
        title = Paragraph(f"<b>Page {page_number}</b>", style)
        story.append(title)
        story.append(Spacer(1, 15))

        paragraphs = html.escape(text).split("\n")

        for paragraph in paragraphs:
            if paragraph.strip():
                text_paragraph = Paragraph(paragraph, style)
                story.append(text_paragraph)
                story.append(Spacer(1, 8))

        story.append(Spacer(1, 20))

    document.build(story)
    return output.getvalue()


# -------------------------------------------------
# UI INPUTS
# -------------------------------------------------
installed_languages = get_ocr_languages()

st.subheader("1️⃣ Select Input Document Language")
ocr_language = st.selectbox(
    "Language in your Image or PDF",
    installed_languages,
    format_func=language_label,
)

st.subheader("2️⃣ Select Translation Language")
target_language_name = st.selectbox(
    "Translate To", sorted(TRANSLATION_LANGUAGES.keys())
)
target_language = TRANSLATION_LANGUAGES[target_language_name]

st.subheader("3️⃣ Upload Image or PDF")
uploaded_file = st.file_uploader(
    "Choose a file", type=["png", "jpg", "jpeg", "pdf"]
)

# -------------------------------------------------
# FILE PROCESSING
# -------------------------------------------------
if uploaded_file:
    try:
        with st.spinner("Reading and translating your document..."):
            file_bytes = uploaded_file.getvalue()
            is_image = "image" in uploaded_file.type

            if is_image:
                input_images = [Image.open(io.BytesIO(file_bytes))]
            else:
                poppler_kwargs = {}
                if os.path.exists(POPPLER_PATH):
                    poppler_kwargs["poppler_path"] = POPPLER_PATH

                input_images = convert_from_bytes(file_bytes, **poppler_kwargs)

            translated_pages = []
            preview_data = []

            progress_bar = st.progress(0)
            total_pages = len(input_images)

            for index, image in enumerate(input_images):
                raw_text = pytesseract.image_to_string(
                    image, lang=ocr_language
                )
                translated_text = safe_translate(raw_text, target_language)

                translated_pages.append(translated_text)
                preview_data.append((raw_text, translated_text))

                percentage = int(((index + 1) / total_pages) * 100)
                progress_bar.progress(percentage)

            progress_bar.empty()

        st.success("✅ Translation completed successfully!")

        # Display results
        for page_number, data in enumerate(preview_data, start=1):
            raw_text, translated_text = data[0], data[1]

            st.subheader(f"📄 Page {page_number}")
            column1, column2 = st.columns(2)

            with column1:
                st.caption("Original Extracted Text")
                st.text_area(
                    "OCR Text",
                    value=raw_text,
                    height=300,
                    key=f"original_{page_number}",
                )

            with column2:
                st.caption("Translated Text")
                st.text_area(
                    "Translation",
                    value=translated_text,
                    height=300,
                    key=f"translated_{page_number}",
                )

        # Combine text for plain text download
        complete_text = "\n\n".join(
            f"--- Page {index + 1} ---\n{text}"
            for index, text in enumerate(translated_pages)
        )

        st.download_button(
            "📥 Download Translated Text",
            data=complete_text.encode("utf-8"),
            file_name="translated.txt",
            mime="text/plain",
        )

        # PDF Download Safeguard
        try:
            pdf_data = create_pdf(translated_pages, target_language)
            st.download_button(
                "📄 Download Translated PDF",
                data=pdf_data,
                file_name="translated.pdf",
                mime="application/pdf",
            )
        except Exception as pdf_err:
            st.warning(
                "Translation succeeded, but PDF generation failed for this target language font."
            )
            st.code(str(pdf_err))

    except Exception as error:
        st.error("❌ Something went wrong while processing the file.")
        st.exception(error)