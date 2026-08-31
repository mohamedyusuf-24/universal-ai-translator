import streamlit as st
from PIL import Image
import pytesseract
from googletrans import Translator, LANGUAGES
from pdf2image import convert_from_bytes
import io
import os
import html
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4

# Windows paths
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

st.set_page_config(page_title="Universal Translator", page_icon="🌍", layout="wide")
st.title("🌍 Universal Multi-Language Translator")
st.write("Upload an image or PDF, extract text with OCR, translate it, and download the result.")

translator = Translator()

# Common OCR languages. Add Tesseract traineddata files for more input languages.
OCR_LANGUAGES = {
    "English": "eng",
    "Tamil": "tam",
    "Hindi": "hin",
    "Arabic": "ara",
    "Chinese Simplified": "chi_sim",
    "Chinese Traditional": "chi_tra",
    "Japanese": "jpn",
    "Korean": "kor",
    "French": "fra",
    "German": "deu",
    "Spanish": "spa",
}

input_lang_name = st.selectbox(
    "Input document language (OCR)",
    list(OCR_LANGUAGES.keys()),
    index=0
)
ocr_lang = OCR_LANGUAGES[input_lang_name]

available_langs = {name.title(): code for code, name in LANGUAGES.items()}
target_lang_name = st.selectbox(
    "Translate to",
    sorted(available_langs.keys())
)
target_code = available_langs[target_lang_name]

uploaded_file = st.file_uploader(
    "Upload Image or PDF",
    type=["png", "jpg", "jpeg", "pdf"]
)

def register_pdf_font(lang_code):
    # Built-in CID fonts handle Chinese, Japanese and Korean in ReportLab.
    if lang_code in ("zh-cn", "zh-tw", "zh"):
        font_name = "STSong-Light"
    elif lang_code == "ja":
        font_name = "HeiseiMin-W3"
    elif lang_code == "ko":
        font_name = "HYSMyeongJo-Medium"
    else:
        return "Helvetica"

    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
    except Exception:
        pass

    return font_name

def make_pdf(translated_pages, font_name):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = font_name
    style.leading = 22

    story = []

    for index, text in enumerate(translated_pages):
        story.append(Paragraph(f"Page {index + 1}", style))
        story.append(Spacer(1, 12))

        # Escape HTML characters while preserving paragraphs.
        paragraphs = html.escape(text).split("\n")
        for paragraph in paragraphs:
            if paragraph.strip():
                story.append(Paragraph(paragraph, style))
                story.append(Spacer(1, 8))

        story.append(Spacer(1, 18))

    doc.build(story)
    return output.getvalue()

if uploaded_file is not None:
    try:
        with st.spinner("Reading, translating and creating your PDF..."):
            if "image" in uploaded_file.type:
                input_images = [Image.open(uploaded_file)]
            else:
                input_images = convert_from_bytes(
                    uploaded_file.read(),
                    poppler_path=POPPLER_PATH
                )

            translated_pages = []
            previews = []

            for image in input_images:
                raw_text = pytesseract.image_to_string(
                    image,
                    lang=ocr_lang
                )

                if raw_text.strip():
                    translated_text = translator.translate(
                        raw_text,
                        dest=target_code
                    ).text
                else:
                    translated_text = "No text detected."

                translated_pages.append(translated_text)
                previews.append((raw_text, translated_text))

            st.success("Translation completed!")

            for page_number, (raw_text, translated_text) in enumerate(previews, start=1):
                st.subheader(f"Page {page_number}")

                col1, col2 = st.columns(2)
                with col1:
                    st.caption("Extracted text")
                    st.text_area(
                        "OCR text",
                        raw_text,
                        height=220,
                        key=f"ocr_{page_number}"
                    )
                with col2:
                    st.caption("Translated text")
                    st.text_area(
                        "Translation",
                        translated_text,
                        height=220,
                        key=f"translation_{page_number}"
                    )

            # Text download works for every Unicode language.
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

            # PDF uses built-in CJK fonts for Chinese/Japanese/Korean.
            # Other scripts may require an appropriate TTF font to render perfectly.
            pdf_font = register_pdf_font(target_code)

            if target_code in ("zh-cn", "zh-tw", "zh", "ja", "ko"):
                pdf_data = make_pdf(translated_pages, pdf_font)

                st.download_button(
                    "📄 Download Translated PDF",
                    data=pdf_data,
                    file_name="translated.pdf",
                    mime="application/pdf"
                )
            else:
                st.info(
                    "Translated text is ready. For best PDF rendering of all scripts, "
                    "add a Unicode font for the selected language."
                )

    except Exception as error:
        st.error("An error occurred while processing the file.")
        st.exception(error)
