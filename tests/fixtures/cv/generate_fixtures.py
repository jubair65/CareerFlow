import os
import sys
from pathlib import Path

# Base directory for fixtures
FIXTURES_DIR = Path(__file__).resolve().parent
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None


def generate_valid_pdf(output_path: Path):
    """
    Generates a clean, valid PDF resume with standard headings:
    Contact, Summary, Skills, Experience, and Education.
    """
    # Raw minimal valid PDF structure with extractable text streams
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 650 >> stream\n"
        b"BT\n"
        b"/F1 18 Tf 50 720 Td (Alex Rahman) Tj\n"
        b"/F1 11 Tf 0 -22 Td (Email: alex.rahman@example.com | Phone: +880 1711-000000 | Location: Dhaka, Bangladesh) Tj\n"
        b"/F1 14 Tf 0 -35 Td (Professional Summary) Tj\n"
        b"/F1 10 Tf 0 -18 Td (Motivated Full Stack Software Engineer with 2+ years of experience building modern web apps.) Tj\n"
        b"/F1 10 Tf 0 -14 Td (Proficient in React, TypeScript, Python, and Django REST framework with measurable impact.) Tj\n"
        b"/F1 14 Tf 0 -30 Td (Technical Skills) Tj\n"
        b"/F1 10 Tf 0 -18 Td (Languages: Python, TypeScript, JavaScript, SQL, HTML5, CSS3) Tj\n"
        b"/F1 10 Tf 0 -14 Td (Frameworks & Libraries: Django, React, FastAPI, Node.js, TailwindCSS) Tj\n"
        b"/F1 10 Tf 0 -14 Td (Databases & Tools: PostgreSQL, MySQL, Redis, Git, Docker, Jest) Tj\n"
        b"/F1 14 Tf 0 -30 Td (Work Experience) Tj\n"
        b"/F1 11 Tf 0 -18 Td (Software Engineer - TechNova Solutions (2024 - Present, 2 years)) Tj\n"
        b"/F1 10 Tf 0 -14 Td (- Engineered modular React frontend components reducing page load time by 35%.) Tj\n"
        b"/F1 10 Tf 0 -14 Td (- Built scalable Django REST APIs serving 15000+ daily active users.) Tj\n"
        b"/F1 14 Tf 0 -30 Td (Education) Tj\n"
        b"/F1 11 Tf 0 -18 Td (BSc in Computer Science & Engineering - BRAC University (Graduated 2023)) Tj\n"
        b"/F1 10 Tf 0 -14 Td (CGPA: 3.82 / 4.00 - Thesis on NLP and Semantic Search) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"0000000247 00000 n \n"
        b"0000000950 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"1020\n"
        b"%%EOF\n"
    )
    output_path.write_bytes(pdf_content)
    print(f"Created valid PDF: {output_path} ({len(pdf_content)} bytes)")


def generate_valid_docx(output_path: Path):
    """
    Generates a valid DOCX resume using python-docx.
    """
    if Document is None:
        print("Warning: python-docx not installed, skipping DOCX generation.")
        return

    doc = Document()
    doc.add_heading('Alex Rahman', level=0)
    p_contact = doc.add_paragraph('Email: alex.rahman@example.com | Phone: +880 1711-000000 | Location: Dhaka, Bangladesh')

    doc.add_heading('Professional Summary', level=1)
    doc.add_paragraph(
        'Motivated Full Stack Software Engineer with 2+ years of experience building modern web applications. '
        'Proficient in React, TypeScript, Python, and Django REST framework with a focus on code quality and clean architecture.'
    )

    doc.add_heading('Technical Skills', level=1)
    doc.add_paragraph('Languages: Python, TypeScript, JavaScript, SQL, HTML5, CSS3')
    doc.add_paragraph('Frameworks: Django, React, FastAPI, Node.js, TailwindCSS')
    doc.add_paragraph('Databases & Tools: PostgreSQL, MySQL, Redis, Git, Docker, Jest')

    doc.add_heading('Work Experience', level=1)
    doc.add_paragraph('Software Engineer — TechNova Solutions (2024 - Present, 2 years)')
    doc.add_paragraph('• Engineered modular React frontend components reducing page load time by 35%.')
    doc.add_paragraph('• Built scalable Django REST APIs serving 15,000+ daily active users.')

    doc.add_heading('Education', level=1)
    doc.add_paragraph('BSc in Computer Science & Engineering — BRAC University (2023)')

    doc.save(str(output_path))
    print(f"Created valid DOCX: {output_path} ({output_path.stat().st_size} bytes)")


def generate_unsupported_png(output_path: Path):
    """Generates an image file to test format rejection (.png)."""
    if Image is not None:
        img = Image.new('RGB', (200, 200), color=(39, 114, 84))
        draw = ImageDraw.Draw(img)
        draw.text((30, 90), "Invalid Resume", fill=(255, 255, 255))
        img.save(str(output_path))
    else:
        # Minimal 1x1 valid PNG binary
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff'
            b'?'
            b'\x00\x05\xfe\x02\xfe\xa7V\x01a\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        output_path.write_bytes(png_bytes)
    print(f"Created unsupported PNG: {output_path} ({output_path.stat().st_size} bytes)")


def generate_oversized_pdf(output_path: Path):
    """
    Generates a PDF file exceeding the 10 MB limit (10.5 MB)
    to test client and server size enforcement.
    """
    header = b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n2 0 obj << /Type /Pages /Kids [] /Count 0 >> endobj\n"
    # Pad to 10.5 MB (11,010,048 bytes)
    target_size = 10 * 1024 * 1024 + 512 * 1024
    padding_needed = target_size - len(header) - 100
    chunk = b"% " + (b"A" * 1022) + b"\n"
    num_chunks = padding_needed // len(chunk)
    footer = b"trailer << /Size 3 /Root 1 0 R >>\nstartxref\n100\n%%EOF\n"

    with open(output_path, 'wb') as f:
        f.write(header)
        for _ in range(num_chunks):
            f.write(chunk)
        f.write(footer)

    print(f"Created oversized PDF: {output_path} ({round(output_path.stat().st_size / (1024*1024), 2)} MB)")


def generate_incomplete_cv(output_path: Path):
    """Generates a minimal one-line CV to test extraction edge cases."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 50 >> stream\n"
        b"BT /F1 12 Tf 50 720 Td (John Doe - Looking for a job.) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n300\n%%EOF\n"
    )
    output_path.write_bytes(content)
    print(f"Created incomplete CV: {output_path}")


def generate_corrupt_file(output_path: Path):
    """Generates a corrupt/malformed PDF file to test error handling."""
    corrupt_bytes = b"%PDF-1.4 CORRUPT CONTENT \x00\x01\x02\xff\xfe\xfd Broken Stream No Catalog Trailer"
    output_path.write_bytes(corrupt_bytes)
    print(f"Created corrupt file: {output_path}")


def main():
    print("Generating Sprint 2 UI Testing Fixtures (UIT-01-T1)...")
    generate_valid_pdf(FIXTURES_DIR / "valid_sample.pdf")
    generate_valid_docx(FIXTURES_DIR / "valid_sample.docx")
    generate_unsupported_png(FIXTURES_DIR / "unsupported_format.png")
    generate_oversized_pdf(FIXTURES_DIR / "oversized_sample.pdf")
    generate_incomplete_cv(FIXTURES_DIR / "incomplete_cv.pdf")
    generate_corrupt_file(FIXTURES_DIR / "corrupt_file.pdf")
    print(f"All test fixtures successfully created in: {FIXTURES_DIR}")


if __name__ == '__main__':
    main()
