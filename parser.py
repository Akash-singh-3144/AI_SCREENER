import os
import PyPDF2
import docx

def extract_text(file_obj, filename: str) -> str:
    """
    Extracts text from a file-like object based on its extension.
    """
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        # Streamlit's UploadedFile behavior allows sequential reads
        if ext == '.pdf':
            return extract_text_from_pdf(file_obj)
        elif ext == '.docx':
            return extract_text_from_docx(file_obj)
        elif ext == '.txt':
            raw_data = file_obj.read()
            if isinstance(raw_data, bytes):
                return raw_data.decode('utf-8', errors='ignore')
            return raw_data
        else:
            return ""
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return ""

def extract_text_from_pdf(file_obj) -> str:
    pdf_reader = PyPDF2.PdfReader(file_obj)
    text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def extract_text_from_docx(file_obj) -> str:
    doc = docx.Document(file_obj)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
