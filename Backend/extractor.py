import os
import fitz  # PyMuPDF


def get_resume_text(file_path):
    """Opens a PDF and pulls out all the plain text from every page."""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return None


if __name__ == "__main__":
    folder_path = "sample_data/"

    if not os.path.exists(folder_path):
        print("Creating sample_data folder. Put some PDF resumes in there and run this again.")
        os.makedirs(folder_path)
    else:
        pdfs = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

        if not pdfs:
            print("No PDFs found. Drop 2 or 3 resumes into the sample_data folder.")
        else:
            print(f"Found {len(pdfs)} resumes to scan.\n")

            for pdf in pdfs:
                full_path = os.path.join(folder_path, pdf)
                extracted_text = get_resume_text(full_path)

                if extracted_text:
                    print(f"[{pdf}]")
                    print(extracted_text[:200] + "...\n")