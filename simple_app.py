"""
تطبيق قارئ العربية البسيط - الإصدار المصغر
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import logging
import mimetypes

# إعداد تسجيل السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تعريف المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# تكوين المنفذ
PORT = int(os.environ.get('PORT', 5000))

class SimpleHandler(BaseHTTPRequestHandler):
    """معالج بسيط للطلبات HTTP"""
    
    def do_GET(self):
        """معالجة طلبات GET"""
        logger.info(f"طلب GET: {self.path}")
        
        if self.path == '/' or self.path == '/index.html':
            # تقديم الصفحة الرئيسية
            self._serve_index()
        elif self.path.startswith('/static/'):
            # تقديم الملفات الثابتة
            self._serve_static_file(self.path[8:])  # إزالة '/static/' من المسار
        else:
            # صفحة 404 للمسارات غير المعروفة
            self.send_error(404, "Page not found")
    
    def _serve_index(self):
        """تقديم صفحة index.html"""
        try:
            with open(os.path.join(TEMPLATES_DIR, 'index.html'), 'rb') as file:
                content = file.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            # إنشاء صفحة بسيطة إذا لم يتم العثور على index.html
            content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Simple Arabic Reader</title>
                <style>
                    body { font-family: Arial; text-align: center; padding: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Simple Arabic Reader</h1>
                    <p>Basic server is running.</p>
                </div>
            </body>
            </html>
            """.encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
    
    def _serve_static_file(self, file_path):
        """تقديم الملفات الثابتة مثل CSS، JS، الصور، إلخ"""
        full_path = os.path.join(STATIC_DIR, file_path)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            self.send_error(404, "File not found")
            return
        
        # تحديد نوع MIME
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # قراءة الملف وإرساله
        with open(full_path, 'rb') as file:
            content = file.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

def run_server():
    """تشغيل الخادم البسيط"""
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, SimpleHandler)
    
    logger.info(f"الخادم يعمل على المنفذ {PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("تم إيقاف الخادم")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()