import os
import zipfile
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from PIL import Image

def generate_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Set Metadata
    def add_metadata(canvas, doc):
        canvas.setAuthor("Nguyen Minh Anh")
        canvas.setSubject("Employee Handbook")
        canvas.setCreator("Microsoft Word 2019")
        canvas.setTitle("BlueMoon Fashion - Employee Handbook 2026")

    content = []
    
    # Title
    content.append(Paragraph("BlueMoon Fashion", styles['Title']))
    content.append(Paragraph("Employee Handbook - v2.4", styles['Heading2']))
    content.append(Spacer(1, 20))
    
    # Body
    text = """
    Welcome to BlueMoon Fashion. This handbook outlines our company policies, 
    culture, and expectations. We are committed to fostering a creative and 
    inclusive environment where every employee can thrive.
    <br/><br/>
    <b>1. Code of Conduct</b><br/>
    All employees are expected to maintain professional behavior and respect 
    colleagues and clients at all times.
    <br/><br/>
    <b>2. IT Security</b><br/>
    Maintain strong passwords and do not share them with anyone. All company 
    devices must be encrypted. Report any suspicious activity to the IT department 
    immediately.
    <br/><br/>
    <b>3. Remote Work Policy</b><br/>
    Employees may work remotely up to three days a week with prior approval 
    from their manager.
    <br/><br/>
    <b>4. Confidentiality</b><br/>
    Internal documents, designs, and customer data are strictly confidential 
    and must not be disclosed outside the company.
    """
    content.append(Paragraph(text, styles['Normal']))
    
    doc.build(content, onFirstPage=add_metadata, onLaterPages=add_metadata)
    print(f"Generated professional PDF: {filename}")

def generate_docx(filename):
    # A .docx is a ZIP file. We create a more realistic XML structure.
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:pPr><w:pStyle w:val="Title"/></w:pPr>
            <w:r><w:t>BlueMoon Fashion - Weekly Synergy Meeting</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Date: March 10, 2026</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>Attendees: Minh Anh, Linda, Mark, Sarah</w:t></w:r>
        </w:p>
        <w:p><w:r><w:t /></w:r></w:p>
        <w:p>
            <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
            <w:r><w:t>Agenda Items</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>1. Q1 Marketing Campaign Review</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>2. New Collection Launch Timeline</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>3. Website Maintenance Feedback</w:t></w:r>
        </w:p>
        <w:p><w:r><w:t /></w:r></w:p>
        <w:p>
            <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
            <w:r><w:t>Notes</w:t></w:r>
        </w:p>
        <w:p>
            <w:r><w:t>The new website portal is almost ready. We need to finalize the user credentials for the deployment team.</w:t></w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>Reminder: temporary password for the dev portal is still set to Summer2026! - Please ensure this is rotated before the public launch.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""

    with zipfile.ZipFile(filename, 'w') as docx:
        docx.writestr('word/document.xml', document_xml)
        docx.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        docx.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    print(f"Generated professional DOCX: {filename}")

def generate_jpg(filename, original_img_path):
    img = Image.open(original_img_path)
    # Convert to RGB if it's RGBA (PNG usually is)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    exif_data = img.getexif()
    # 315 = Artist, 305 = Software
    exif_data[315] = "Minh Anh"
    exif_data[305] = "Photoshop 2026"
    
    # Save as JPG with EXIF
    img.save(filename, "JPEG", exif=exif_data, quality=95)
    print(f"Generated professional JPG from {original_img_path}: {filename}")

if __name__ == "__main__":
    assets_dir = "/home/ntlong/Desktop/Lab/bangiaolab/image_extraction/web/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    generate_pdf(os.path.join(assets_dir, "employee_handbook.pdf"))
    generate_docx(os.path.join(assets_dir, "meeting_notes.docx"))
    
    original_office_img = os.path.join(assets_dir, "office_original.png")
    if os.path.exists(original_office_img):
        generate_jpg(os.path.join(assets_dir, "office.jpg"), original_office_img)
    else:
        print("Original office image not found, skipping JPG generation.")
