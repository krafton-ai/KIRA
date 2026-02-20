---
name: pdf
description: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see reference.md. If you need to fill out a PDF form, read forms.md and follow its instructions.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - Create PDFs

#### Basic PDF Creation
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Add text
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Add a line
c.line(100, height - 140, 400, height - 140)

# Save
c.save()
```

#### Create PDF with Multiple Pages
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Add content
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Build PDF
doc.build(story)
```

#### Korean Font Support (한글 폰트 지원)

**CRITICAL**: reportlab은 기본적으로 한글을 지원하지 않습니다. 한글을 사용하려면 시스템의 한글 폰트를 찾아서 등록해야 합니다.

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import platform
import os

def get_korean_font_path():
    """시스템의 한글 폰트 경로를 찾습니다."""
    system = platform.system()

    if system == 'Darwin':  # macOS
        fonts = [
            '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
            '/System/Library/Fonts/Supplemental/AppleMyungjo.ttf',
            '/Library/Fonts/NanumGothic.ttf'
        ]
    elif system == 'Windows':
        fonts = [
            'C:\\Windows\\Fonts\\malgun.ttf',  # 맑은 고딕
            'C:\\Windows\\Fonts\\gulim.ttc',   # 굴림
            'C:\\Windows\\Fonts\\batang.ttc'   # 바탕
        ]
    else:  # Linux
        fonts = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
        ]

    # 존재하는 첫 번째 폰트 반환
    for font_path in fonts:
        if os.path.exists(font_path):
            return font_path

    raise FileNotFoundError("한글 폰트를 찾을 수 없습니다. 시스템에 한글 폰트를 설치해주세요.")

# 한글 폰트 등록
korean_font_path = get_korean_font_path()
pdfmetrics.registerFont(TTFont('KoreanFont', korean_font_path))

# PDF 생성
c = canvas.Canvas("korean.pdf", pagesize=letter)
width, height = letter

# 한글 폰트 설정
c.setFont('KoreanFont', 12)

# 한글 텍스트 추가
c.drawString(100, height - 100, "안녕하세요! 한글 PDF 생성 테스트입니다.")
c.drawString(100, height - 120, "시스템의 한글 폰트를 자동으로 찾아서 사용합니다.")

c.save()
```

**Platypus (고급 레이아웃)에서 한글 사용:**
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import platform
import os

def get_korean_font_path():
    """시스템의 한글 폰트 경로를 찾습니다."""
    system = platform.system()

    if system == 'Darwin':  # macOS
        fonts = [
            '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
            '/System/Library/Fonts/Supplemental/AppleMyungjo.ttf',
            '/Library/Fonts/NanumGothic.ttf'
        ]
    elif system == 'Windows':
        fonts = [
            'C:\\Windows\\Fonts\\malgun.ttf',  # 맑은 고딕
            'C:\\Windows\\Fonts\\gulim.ttc',   # 굴림
            'C:\\Windows\\Fonts\\batang.ttc'   # 바탕
        ]
    else:  # Linux
        fonts = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
        ]

    for font_path in fonts:
        if os.path.exists(font_path):
            return font_path

    raise FileNotFoundError("한글 폰트를 찾을 수 없습니다.")

# 한글 폰트 등록
korean_font_path = get_korean_font_path()
pdfmetrics.registerFont(TTFont('KoreanFont', korean_font_path))

# 한글용 스타일 생성
styles = getSampleStyleSheet()
korean_style = ParagraphStyle(
    'Korean',
    parent=styles['Normal'],
    fontName='KoreanFont',
    fontSize=12,
    leading=18
)

korean_title = ParagraphStyle(
    'KoreanTitle',
    parent=styles['Title'],
    fontName='KoreanFont',
    fontSize=24,
    leading=30
)

# PDF 생성
doc = SimpleDocTemplate("korean_report.pdf", pagesize=letter)
story = []

# 한글 콘텐츠 추가
title = Paragraph("한글 리포트 제목", korean_title)
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("이것은 한글로 작성된 본문입니다. 시스템의 한글 폰트를 자동으로 찾아서 사용합니다.", korean_style)
story.append(body)

doc.build(story)
```

**IMPORTANT**:
- 한글 텍스트가 포함된 PDF를 생성할 때는 **반드시** 위의 `get_korean_font_path()` 함수를 사용하여 한글 폰트를 등록해야 합니다.
- Canvas 사용 시: `c.setFont('KoreanFont', font_size)`
- Platypus 사용 시: `ParagraphStyle`에서 `fontName='KoreanFont'` 지정

## Command-Line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create watermark (or load existing)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extract Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see forms.md) | See forms.md |

## Next Steps

- For advanced pypdfium2 usage, see reference.md
- For JavaScript libraries (pdf-lib), see reference.md
- If you need to fill out a PDF form, follow the instructions in forms.md
- For troubleshooting guides, see reference.md
