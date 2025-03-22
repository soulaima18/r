"""
تطبيق قارئ النصوص العربية الاحتياطي
تم تصميمه لتشغيل التطبيق بأقل المتطلبات الممكنة ودون الاعتماد على مكتبات خارجية
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import json
import logging
import sys
import threading
import uuid
import time

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# تعريف المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')

# إنشاء مجلد التحميلات إذا لم يكن موجوداً
os.makedirs(UPLOADS_DIR, exist_ok=True)

# تكوين المنفذ
PORT = int(os.environ.get('PORT', 5000))

# تخزين حالة التطبيق
app_state = {
    'processing_files': {},  # لتتبع حالة معالجة الملفات
}


class MinimalArabicReader(BaseHTTPRequestHandler):
    """معالج طلبات HTTP للقارئ العربي البسيط"""
    
    def _set_response_headers(self, status_code=200, content_type='text/html'):
        """ضبط رؤوس الاستجابة"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def do_GET(self):
        """معالجة طلبات GET"""
        logger.info(f"طلب GET: {self.path}")
        
        if self.path == '/' or self.path == '/index.html':
            # تقديم الصفحة الرئيسية
            self._serve_file(os.path.join(TEMPLATES_DIR, 'index.html'))
        elif self.path.startswith('/static/'):
            # تقديم الملفات الثابتة
            file_path = self.path[8:]  # إزالة '/static/' من المسار
            self._serve_file(os.path.join(STATIC_DIR, file_path))
        elif self.path.startswith('/api/status/'):
            # حالة معالجة الملف
            file_id = self.path.split('/')[-1]
            self._serve_json(self._get_processing_status(file_id))
        else:
            # صفحة 404 للمسارات غير المعروفة
            self._set_response_headers(404)
            self.wfile.write(b'Page Not Found')
    
    def do_POST(self):
        """معالجة طلبات POST"""
        logger.info(f"طلب POST: {self.path}")
        
        if self.path == '/api/process-text':
            # معالجة النص المدخل
            self._process_text_input()
        elif self.path == '/api/upload-file':
            # معالجة الملف المرفوع
            self._process_file_upload()
        else:
            # صفحة 404 للمسارات غير المعروفة
            self._set_response_headers(404)
            self.wfile.write(b'API Endpoint Not Found')
    
    def _serve_file(self, file_path):
        """تقديم ملف من نظام الملفات"""
        if not os.path.exists(file_path):
            # إذا كانت index.html غير موجودة، قدم الصفحة الافتراضية
            if file_path.endswith('index.html'):
                self._serve_default_page()
                return
            else:
                self._set_response_headers(404)
                self.wfile.write(b'File Not Found')
                return
        
        # تحديد نوع المحتوى بناءً على امتداد الملف
        content_type = 'text/html'
        if file_path.endswith('.css'):
            content_type = 'text/css'
        elif file_path.endswith('.js'):
            content_type = 'application/javascript'
        elif file_path.endswith('.png'):
            content_type = 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        
        self._set_response_headers(200, content_type)
        
        # قراءة وإرسال الملف
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())
    
    def _serve_default_page(self):
        """تقديم الصفحة الافتراضية عندما لا تكون index.html موجودة"""
        self._set_response_headers(200)
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Arabic Reader Fallback</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #4a54f1;
                }
                textarea {
                    width: 100%;
                    height: 200px;
                    margin: 20px 0;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                }
                button {
                    background-color: #4a54f1;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #3a44e1;
                }
                .output {
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                    text-align: right;
                    min-height: 100px;
                    border: 1px solid #ddd;
                }
                .controls {
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Arabic Text Reader - Fallback Version</h1>
                <p>Enter Arabic text below or upload a text file</p>
                
                <textarea id="textInput" placeholder="Enter Arabic text here..." dir="rtl"></textarea>
                
                <div>
                    <input type="file" id="fileInput" accept=".txt,.text">
                    <button onclick="processText()">Process Text</button>
                </div>
                
                <div class="output" id="output" dir="rtl"></div>
                
                <div class="controls">
                    <button id="playButton" onclick="toggleSpeech()">Start Reading</button>
                    <select id="speedControl">
                        <option value="0.5">Slow (0.5x)</option>
                        <option value="1" selected>Normal (1x)</option>
                        <option value="1.5">Fast (1.5x)</option>
                        <option value="2">Very Fast (2x)</option>
                    </select>
                </div>
            </div>
            
            <script>
                // Variables
                let isPlaying = false;
                let speech = new SpeechSynthesisUtterance();
                let textChunks = [];
                let currentChunkIndex = 0;
                
                // Setup speech synthesis
                speech.lang = 'ar-SA';
                speech.onend = function() {
                    currentChunkIndex++;
                    if(currentChunkIndex < textChunks.length && isPlaying) {
                        speakChunk();
                    } else {
                        isPlaying = false;
                        document.getElementById('playButton').textContent = 'Start Reading';
                    }
                };
                
                // Initialize speech synthesis
                window.speechSynthesis.onvoiceschanged = function() {
                    let voices = window.speechSynthesis.getVoices();
                    // Try to find an Arabic voice
                    let arabicVoice = voices.find(voice => 
                        voice.lang.includes('ar') || 
                        voice.name.toLowerCase().includes('arab')
                    );
                    
                    if (arabicVoice) {
                        speech.voice = arabicVoice;
                    }
                };
                
                // Process text from textarea
                function processText() {
                    const text = document.getElementById('textInput').value.trim();
                    if(text) {
                        document.getElementById('output').innerText = text;
                        
                        // Prepare text for reading
                        textChunks = splitIntoChunks(text);
                        currentChunkIndex = 0;
                    }
                }
                
                // Handle file upload
                document.getElementById('fileInput').addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if(file) {
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            document.getElementById('textInput').value = e.target.result;
                            processText();
                        };
                        reader.readAsText(file);
                    }
                });
                
                // Toggle speech
                function toggleSpeech() {
                    if(textChunks.length === 0) {
                        processText();
                    }
                    
                    if(isPlaying) {
                        isPlaying = false;
                        window.speechSynthesis.cancel();
                        document.getElementById('playButton').textContent = 'Start Reading';
                    } else {
                        isPlaying = true;
                        document.getElementById('playButton').textContent = 'Pause';
                        speakChunk();
                    }
                }
                
                // Speak current chunk
                function speakChunk() {
                    if(currentChunkIndex < textChunks.length) {
                        speech.text = textChunks[currentChunkIndex];
                        speech.rate = parseFloat(document.getElementById('speedControl').value);
                        window.speechSynthesis.speak(speech);
                    }
                }
                
                // Split text into manageable chunks
                function splitIntoChunks(text, maxLength = 200) {
                    let chunks = [];
                    let sentences = text.split(/[.!?،؛]/);
                    
                    let currentChunk = "";
                    for(let sentence of sentences) {
                        if(sentence.trim() === "") continue;
                        
                        if((currentChunk + sentence).length < maxLength) {
                            currentChunk += sentence + ". ";
                        } else {
                            if(currentChunk) chunks.push(currentChunk);
                            currentChunk = sentence + ". ";
                        }
                    }
                    
                    if(currentChunk) chunks.push(currentChunk);
                    return chunks;
                }
                
                // Update speech rate when changed
                document.getElementById('speedControl').addEventListener('change', function() {
                    speech.rate = parseFloat(this.value);
                });
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def _serve_json(self, data):
        """تقديم استجابة JSON"""
        self._set_response_headers(200, 'application/json')
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _read_post_data(self):
        """قراءة بيانات POST"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        return post_data
    
    def _process_text_input(self):
        """معالجة النص المدخل"""
        try:
            post_data = self._read_post_data()
            data = json.loads(post_data.decode('utf-8'))
            
            text = data.get('text', '')
            
            # معالجة النص
            processed_text = self._basic_text_processing(text)
            
            # إرجاع النص المعالج
            self._serve_json({
                'status': 'success',
                'text': processed_text
            })
            
        except Exception as e:
            logger.error(f"خطأ في معالجة النص: {e}")
            self._serve_json({
                'status': 'error',
                'message': str(e)
            })
    
    def _process_file_upload(self):
        """معالجة الملف المرفوع"""
        try:
            # تحليل بيانات النموذج
            content_type = self.headers['Content-Type']
            
            # التحقق من نوع المحتوى
            if not content_type.startswith('multipart/form-data'):
                self._serve_json({
                    'status': 'error',
                    'message': 'نوع المحتوى غير صحيح. يجب أن يكون multipart/form-data'
                })
                return
            
            # قراءة بيانات النموذج
            import cgi
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # التحقق من وجود ملف
            if 'file' not in form:
                self._serve_json({
                    'status': 'error',
                    'message': 'لم يتم العثور على ملف'
                })
                return
            
            # الحصول على الملف
            file_item = form['file']
            
            # التحقق من وجود اسم الملف
            if not file_item.filename:
                self._serve_json({
                    'status': 'error',
                    'message': 'لم يتم اختيار ملف'
                })
                return
            
            # إنشاء معرف فريد للملف
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file_item.filename)[1].lower()
            safe_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(UPLOADS_DIR, safe_filename)
            
            # حفظ الملف
            with open(file_path, 'wb') as file:
                file.write(file_item.file.read())
            
            # بدء معالجة الملف في خلفية النظام
            app_state['processing_files'][file_id] = {
                'status': 'processing',
                'progress': 0,
                'filename': file_item.filename,
                'path': file_path
            }
            
            threading.Thread(target=self._process_file_in_background, args=(file_id, file_path)).start()
            
            # إرجاع معرف الملف للاستعلام عن حالة المعالجة
            self._serve_json({
                'status': 'processing',
                'file_id': file_id,
                'message': 'جاري معالجة الملف'
            })
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الملف المرفوع: {e}")
            self._serve_json({
                'status': 'error',
                'message': str(e)
            })
    
    def _process_file_in_background(self, file_id, file_path):
        """معالجة الملف في خلفية النظام"""
        try:
            # تحديث الحالة
            app_state['processing_files'][file_id]['progress'] = 10
            
            # قراءة الملف
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                text = file.read()
            
            # تحديث الحالة
            app_state['processing_files'][file_id]['progress'] = 40
            
            # معالجة النص
            processed_text = self._basic_text_processing(text)
            
            # تحديث الحالة
            app_state['processing_files'][file_id]['progress'] = 80
            
            # محاكاة العمل الإضافي
            time.sleep(1)
            
            # الانتهاء من المعالجة
            app_state['processing_files'][file_id].update({
                'status': 'completed',
                'progress': 100,
                'text': processed_text
            })
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الملف {file_id}: {e}")
            app_state['processing_files'][file_id].update({
                'status': 'error',
                'progress': 0,
                'error': str(e)
            })
        finally:
            # حذف الملف بعد المعالجة
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def _get_processing_status(self, file_id):
        """الحصول على حالة معالجة الملف"""
        if file_id not in app_state['processing_files']:
            return {
                'status': 'error',
                'message': 'لم يتم العثور على معرف الملف'
            }
        
        return app_state['processing_files'][file_id]
    
    def _basic_text_processing(self, text):
        """معالجة النص الأساسية"""
        # التحقق من النص
        if not text:
            return ""
        
        # تنظيف المسافات المتعددة
        text = ' '.join(text.split())
        
        # تقسيم النص إلى فقرات
        paragraphs = []
        
        for paragraph in text.split('\n'):
            if paragraph.strip():
                # إضافة علامات HTML للعرض بالاتجاه الصحيح
                paragraphs.append(f'<p dir="rtl" lang="ar">{paragraph.strip()}</p>')
        
        # دمج الفقرات
        processed_text = '\n'.join(paragraphs)
        
        # إضافة غلاف HTML للتأكد من العرض بالاتجاه الصحيح
        processed_text = f'<div dir="rtl" class="arabic-text">{processed_text}</div>'
        
        return processed_text


def run_server():
    """تشغيل الخادم على المنفذ المحدد"""
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, MinimalArabicReader)
    
    logger.info(f"بدء تشغيل خادم القارئ العربي البسيط على المنفذ {PORT}")
    logger.info(f"يمكنك الوصول للتطبيق عبر الرابط: http://localhost:{PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تشغيل الخادم: {e}")
    finally:
        httpd.server_close()
        logger.info("تم إغلاق الخادم")


if __name__ == "__main__":
    run_server()