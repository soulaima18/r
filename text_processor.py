import re
import logging
import io
import os
from PIL import Image

# تعريف قائمة بمكتبات PDF بديلة للاستخدام
PDF_LIBRARIES_AVAILABLE = False

# محاولة استيراد مكتبات PDF مع معالجة الاستثناءات
try:
    from PyPDF2 import PdfReader
    import pdfplumber
    PDF_LIBRARIES_AVAILABLE = True
except ImportError:
    # رسالة تحذير في حالة عدم توفر مكتبات PDF
    logging.warning("لم يتم العثور على مكتبات PDF (PyPDF2 أو pdfplumber). بعض وظائف المعالجة قد لا تعمل.")
    
    # تعريف كلاسات وهمية للتوافق
    class PdfReader:
        def __init__(self, *args, **kwargs):
            pass
        @property
        def pages(self):
            return []
            
    class PdfPage:
        def extract_text(self):
            return ""

# محاولة استيراد pytesseract مع معالجة استثناءات
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("لم يتم العثور على مكتبة pytesseract. لن تتوفر وظائف التعرف الضوئي على النصوص.")

def clean_arabic_text(text):
    """
    Clean text to keep only Arabic characters and proper spacing.
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: Cleaned Arabic text with proper paragraphs
    """
    if not text or text.strip() == "":
        return '<p dir="rtl" lang="ar" class="arabic-text">لا يوجد نص لعرضه</p>'
    
    # المشكلة الأساسية: علامات التوجيه للنص العربي مقلوبة
    # هذه خطوات لتصحيح اتجاه النص:
    
    # 1. أولاً: تنظيف رموز التحكم الخاصة باتجاه النص التي تسبب المشاكل
    for char in ['\u200E', '\u200F', '\u202A', '\u202B', '\u202C', '\u202D', '\u202E', '\u2066', '\u2067', '\u2068', '\u2069']:
        text = text.replace(char, '')
    
    # 2. التحقق ما إذا كان النص مقلوباً (يحتوي على أحرف عربية متسلسلة في الاتجاه الخاطئ)
    # إذا كان النص مقلوباً، يتم تطبيق خوارزمية العكس لإصلاحه
    reversed_chars = 0
    total_chars = 0
    
    # نتحقق من كل حرف عربي - إذا كان هناك الكثير من حالات الانعكاس، فالنص مقلوب
    for i in range(len(text) - 1):
        if ('\u0600' <= text[i] <= '\u06FF' or '\u0750' <= text[i] <= '\u077F' or 
            '\u08A0' <= text[i] <= '\u08FF' or '\uFB50' <= text[i] <= '\uFDFF' or 
            '\uFE70' <= text[i] <= '\uFEFF'):
            total_chars += 1
            if ('\u0600' <= text[i+1] <= '\u06FF' or '\u0750' <= text[i+1] <= '\u077F' or 
                '\u08A0' <= text[i+1] <= '\u08FF' or '\uFB50' <= text[i+1] <= '\uFDFF' or 
                '\uFE70' <= text[i+1] <= '\uFEFF'):
                if ord(text[i]) < ord(text[i+1]) and text[i] != ' ' and text[i+1] != ' ':
                    reversed_chars += 1
    
    # إذا كانت نسبة الأحرف المقلوبة عالية (أكثر من 30%)، فافترض أن كامل النص مقلوب
    is_reversed = False
    if total_chars > 0 and reversed_chars / total_chars > 0.3:
        # نعكس النص كلياً بدلاً من الاعتماد على علامات HTML فقط
        text = text[::-1]  # هذا يعكس سلسلة النص بالكامل
        is_reversed = True
    
    # 3. الاحتفاظ بالنص العربي والأرقام وعلامات الترقيم فقط
    arabic_pattern = r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF0-9\s\.\,\?\!\:\;\(\)\[\]\{\}\-\"\«\»\؟\،\؛]+'
    cleaned_text = re.sub(arabic_pattern, ' ', text)
    
    # 4. تنظيف المسافات الزائدة مع الحفاظ على فواصل الفقرات
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # 5. تقسيم النص إلى فقرات ذات معنى وإضافة علامات HTML المناسبة
    paragraphs = []
    chunks = re.split(r'\n{2,}', cleaned_text)
    
    for chunk in chunks:
        # معالجة كل فقرة محتملة
        lines = chunk.split('\n')
        processed_lines = []
        for line in lines:
            if line.strip():  # الاحتفاظ بالأسطر غير الفارغة فقط
                processed_lines.append(line.strip())
        
        if processed_lines:
            # دمج الأسطر في فقرة واحدة
            paragraph = ' '.join(processed_lines)
            # إصلاح قضايا المسافات بين الكلمات العربية
            paragraph = re.sub(r'([^\s])(\s{2,})([^\s])', r'\1 \3', paragraph)
            paragraphs.append(paragraph)
    
    # معالجة الفقرات وإضافة علامات HTML لضمان عرض النص بالاتجاه الصحيح
    filtered_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and len(p.split()) > 1:  # الاحتفاظ بالفقرات التي تحتوي على كلمتين على الأقل
            # لا نضيف علامات HTML الاتجاهية إذا كان النص تم عكسه بالفعل
            if is_reversed:
                p = f'<p dir="rtl" lang="ar" class="arabic-text">{p}</p>'
            else:
                # تغليف كامل ومحكم للعرض بالاتجاه الصحيح
                p = f'<p dir="rtl" lang="ar" style="text-align: right; unicode-bidi: bidi-override;" class="arabic-text">{p}</p>'
            filtered_paragraphs.append(p)
    
    # إذا لم نحصل على فقرات حقيقية، استخدم نهجًا مختلفًا
    if not filtered_paragraphs and cleaned_text.strip():
        # تقسيم النص إلى جمل أولاً
        sentences = re.split(r'[\.!?؟,،;؛\n]', cleaned_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            # جمع الجمل في فقرات
            current_paragraph = []
            for sentence in sentences:
                if sentence:
                    current_paragraph.append(sentence)
                    # الحفاظ على فقرات بطول معقول
                    if len(' '.join(current_paragraph).split()) > 15:
                        paragraph = ' '.join(current_paragraph)
                        if is_reversed:
                            paragraph = f'<p dir="rtl" lang="ar" class="arabic-text">{paragraph}</p>'
                        else:
                            paragraph = f'<p dir="rtl" lang="ar" style="text-align: right; unicode-bidi: bidi-override;" class="arabic-text">{paragraph}</p>'
                        filtered_paragraphs.append(paragraph)
                        current_paragraph = []
            
            # إضافة أي محتوى متبقي
            if current_paragraph:
                paragraph = ' '.join(current_paragraph)
                if is_reversed:
                    paragraph = f'<p dir="rtl" lang="ar" class="arabic-text">{paragraph}</p>'
                else:
                    paragraph = f'<p dir="rtl" lang="ar" style="text-align: right; unicode-bidi: bidi-override;" class="arabic-text">{paragraph}</p>'
                filtered_paragraphs.append(paragraph)
    
    # إذا كنا ما زلنا لا نملك شيئًا، استخدم النص بالكامل
    if not filtered_paragraphs and cleaned_text.strip():
        if is_reversed:
            filtered_paragraphs = [f'<p dir="rtl" lang="ar" class="arabic-text">{cleaned_text.strip()}</p>']
        else:
            filtered_paragraphs = [f'<p dir="rtl" lang="ar" style="text-align: right; unicode-bidi: bidi-override;" class="arabic-text">{cleaned_text.strip()}</p>']
    
    # دمج الفقرات وإضافة غلاف RTL على مستوى المستند
    if filtered_paragraphs:
        final_text = '\n\n'.join(filtered_paragraphs)
    else:
        final_text = f'<p dir="rtl" lang="ar" style="text-align: right; unicode-bidi: bidi-override;" class="arabic-text">لا يمكن تنظيم النص بشكل صحيح</p>'
    
    # إضافة غلاف RTL إضافي للتأكد من العرض الصحيح
    final_text = f'<div dir="rtl" style="text-align: right;" class="rtl-text-container">{final_text}</div>'
    
    return final_text

def extract_text_with_pdfplumber(pdf_path):
    """
    Extract text from a PDF file using pdfplumber.
    Often better for complex layouts and tables.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of text content by page
    """
    try:
        all_pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                if page_text:
                    # Process tables separately to preserve structure
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_text = "\n".join([" | ".join([cell or "" for cell in row]) for row in table])
                            if table_text:
                                page_text += f"\n\n{table_text}\n"
                    
                    all_pages.append(page_text)
                else:
                    all_pages.append("")  # Empty page
        
        return all_pages
    except Exception as e:
        logging.error(f"Error extracting text with pdfplumber: {str(e)}")
        return []

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using multiple methods for better results.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text organized by pages
    """
    try:
        # Try pdfplumber first (better for preserving layout)
        plumber_pages = extract_text_with_pdfplumber(pdf_path)
        
        # If pdfplumber extracted reasonable text, use it
        if plumber_pages and any(p.strip() for p in plumber_pages):
            # Create a proper page break structure
            pages_text = []
            for i, page_text in enumerate(plumber_pages):
                if page_text.strip():
                    header = f"// صفحة {i+1}\n"
                    pages_text.append(f"{header}{page_text}")
                
            return "\n\n".join(pages_text)
        
        # Fallback to PyPDF2
        reader = PdfReader(pdf_path)
        pages_text = []
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                header = f"// صفحة {i+1}\n"
                pages_text.append(f"{header}{page_text}")
        
        if pages_text:
            return "\n\n".join(pages_text)
        
        # If text extraction returns empty, the PDF might be image-based
        logging.warning("PDF may be image-based. No text extracted.")
        return "لا يمكن استخراج النص من هذا الملف. قد يكون الملف يحتوي على صور فقط."
        
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        raise
