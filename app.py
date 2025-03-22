import os
import re
import uuid
import tempfile
import logging
from flask import Flask, render_template, request, jsonify

from utils.text_processor import clean_arabic_text, extract_text_from_pdf

# بديل لـ secure_filename من werkzeug
def secure_filename(filename):
    """تنظيف اسم الملف ليكون آمنًا لاستخدامه في نظام الملفات."""
    keepcharacters = (' ', '.', '_', '-')
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).strip()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secure_key")

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    """Process uploaded PDF files and extract Arabic text."""
    if 'file' not in request.files:
        return jsonify({'error': 'لم يتم العثور على ملف'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار ملف'}), 400
    
    # تحسين الأداء: تقييد حجم الملف وزمن المعالجة
    MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB للملفات الكبيرة
    MAX_PROCESSING_TIME = 90  # 90 ثانية للمعالجة
    
    if file and file.filename.lower().endswith('.pdf'):
        # استخدام معرف فريد لكل عملية
        operation_id = str(uuid.uuid4())
        temp_path = None
        
        try:
            # التحقق من حجم الملف أولاً لتجنب أخطاء التوقف
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                logging.warning(f"File too large: {file_size} bytes")
                return jsonify({
                    'error': 'الملف كبير جداً. حجم الملف الأقصى هو 30 ميجابايت',
                    'details': 'يرجى تقسيم الملف الكبير إلى أجزاء أصغر لمعالجة أفضل'
                }), 413
            
            # إنشاء مجلد مؤقت مخصص إذا لم يكن موجوداً
            temp_folder = os.path.join(tempfile.gettempdir(), 'arabic_reader_tmp')
            os.makedirs(temp_folder, exist_ok=True)
            
            # حفظ الملف المرفوع باسم فريد لمنع التعارضات
            safe_filename = secure_filename(file.filename)
            temp_path = os.path.join(temp_folder, f"{operation_id}_{safe_filename}")
            file.save(temp_path)
            
            # تحديد سياق المهلة للمعالجة
            import signal
            from contextlib import contextmanager
            
            @contextmanager
            def time_limit(seconds):
                def signal_handler(signum, frame):
                    raise TimeoutError("تجاوز الوقت المسموح لمعالجة الملف")
                signal.signal(signal.SIGALRM, signal_handler)
                signal.alarm(seconds)
                try:
                    yield
                finally:
                    signal.alarm(0)
            
            # معالجة الملف مع حماية المهلة
            extracted_text = ""
            try:
                with time_limit(MAX_PROCESSING_TIME):
                    # استخراج النص من ملف PDF باستخدام وظائف متعددة
                    extracted_text = extract_text_from_pdf(temp_path)
            except TimeoutError as e:
                logging.error(f"Processing timeout for {operation_id}: {str(e)}")
                # تنظيف الملف المؤقت
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                return jsonify({
                    'error': 'استغرق الملف وقتاً طويلاً للمعالجة. يرجى تحميل ملف أصغر',
                    'details': 'قسّم الملف إلى أجزاء بحجم 20-30 ميجابايت لضمان معالجة أسرع'
                }), 408
            
            # نجاح استخراج النص، الآن نعالجه حسب الصفحات
            # البحث عن علامات الصفحة مثل "// صفحة X"
            page_pattern = r'\/\/ صفحة \d+\n'
            
            # تهيئة قائمة صفحات فارغة
            pages = []
            
            # تحقق مما إذا كانت لدينا علامات صفحة موجودة بالفعل
            if re.search(page_pattern, extracted_text):
                # تقسيم النص حسب علامات الصفحة
                raw_pages = re.split(r'\n\n(?=\/\/ صفحة \d+\n)', extracted_text)
                
                # معالجة كل صفحة لضمان عرض RTL المناسب
                for page in raw_pages:
                    if not page.strip():
                        continue
                        
                    # استخراج رأس الصفحة
                    header_match = re.match(page_pattern, page)
                    header = ""
                    content = page
                    
                    if header_match:
                        header = header_match.group(0)
                        content = page[len(header):]
                    
                    # تنظيف المحتوى - يضيف تلقائياً علامات RTL المناسبة الآن
                    cleaned_content = clean_arabic_text(content)
                    
                    # إعادة بناء الصفحة
                    pages.append(f"{header}{cleaned_content}")
            else:
                # لا توجد علامات صفحة، نحتاج إلى تقسيم النص إلى صفحات منطقية
                # تنظيف النص أولاً
                clean_text = clean_arabic_text(extracted_text)
                
                # تقسيم النص إلى فقرات
                raw_paragraphs = clean_text.split('\n\n')
                paragraphs = [p for p in raw_paragraphs if p.strip()]
                
                # حساب حجم صفحة معقول استنادًا إلى عدد الفقرات
                # للوثائق الكبيرة، استخدم المزيد من الفقرات لكل صفحة
                paragraphs_per_page = max(1, min(3, len(paragraphs) // 10))
                
                # تجميع الفقرات في صفحات
                for i in range(0, len(paragraphs), paragraphs_per_page):
                    page_content = '\n\n'.join(paragraphs[i:i+paragraphs_per_page])
                    if page_content.strip():
                        header = f"// صفحة {(i // paragraphs_per_page) + 1}\n"
                        pages.append(f"{header}{page_content}")
            
            # تنظيف الملف المؤقت
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            
            # إعادة النص المعالج، جاهز للعرض
            return jsonify({
                'status': 'success', 
                'pages': pages,
                'totalPages': len(pages)
            })
            
        except Exception as e:
            # تسجيل الخطأ لتصحيح الأخطاء
            logging.error(f"Error processing PDF {operation_id}: {str(e)}")
            
            # دائمًا نظف الملفات المؤقتة
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
                
            # إعادة خطأ مفهوم للمستخدم
            return jsonify({
                'error': 'حدث خطأ أثناء معالجة ملف PDF',
                'details': 'يرجى التأكد من أن الملف بتنسيق PDF صالح وأن حجمه أقل من 30 ميجابايت'
            }), 500

# Helper function to fix bidirectional text issues
def fix_bidi_text(text):
    """Fix bidirectional text issues that cause character reversal"""
    # Add explicit RTL markers to ensure proper rendering
    text = text.replace('\u202E', '')  # Remove any existing RTL override
    
    # Fix common issues with spacing between Arabic words
    text = re.sub(r'([\u0600-\u06FF])\s+([\u0600-\u06FF])', r'\1 \2', text)
    
    # Ensure proper word spacing
    text = re.sub(r'\s{2,}', ' ', text)
    
    # Wrap in HTML with RTL support for better display
    if not text.startswith('<p'):
        text = f"<p dir='rtl'>{text}</p>"
        
    return text

@app.route('/process-text', methods=['POST'])
def process_text():
    """Process uploaded text files."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith(('.txt', '.text')):
        try:
            content = file.read().decode('utf-8', errors='replace')
            
            # Clean the text
            clean_text = clean_arabic_text(content)
            clean_text = fix_bidi_text(clean_text)
            
            # Split into paragraphs
            paragraphs = [p for p in clean_text.split('\n\n') if p.strip()]
            
            # Create pages with headers
            pages = []
            for i, paragraph in enumerate(paragraphs):
                header = f"// صفحة {i+1}\n"
                # Make sure it's wrapped in RTL paragraph
                if not paragraph.startswith('<p'):
                    paragraph = f"<p dir='rtl'>{paragraph}</p>"
                pages.append(f"{header}{paragraph}")
            
            return jsonify({
                'status': 'success', 
                'pages': pages,
                'totalPages': len(pages)
            })
            
        except Exception as e:
            logging.error(f"Error processing text file: {str(e)}")
            return jsonify({'error': f'حدث خطأ أثناء معالجة الملف النصي: {str(e)}'}), 500
    
    return jsonify({'error': 'نوع ملف غير صالح. يرجى تحميل ملف PDF أو ملف نصي.'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
