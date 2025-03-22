"""
خادم HTTP بسيط لتقديم تطبيق القارئ العربي
"""

import os
import http.server
import socketserver
import logging

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# تعريف المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# تكوين المنفذ
PORT = int(os.environ.get('PORT', 5000))

class ArabicReaderHandler(http.server.SimpleHTTPRequestHandler):
    """
    معالج مخصص للطلبات HTTP
    يقوم بتوجيه المسارات وتقديم الملفات الثابتة
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """
        معالجة طلبات GET
        توجيه المسار الرئيسي إلى قالب index.html
        وتوجيه المسارات الأخرى إلى الملفات الثابتة
        """
        logger.info(f"طلب GET: {self.path}")
        
        # معالجة المسار الرئيسي
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # قراءة قالب index.html
            try:
                with open(os.path.join(TEMPLATE_DIR, 'index.html'), 'rb') as file:
                    self.wfile.write(file.read())
            except FileNotFoundError:
                # إنشاء صفحة HTML بسيطة (فقط ASCII)
                html_content = """
                <!DOCTYPE html>
                <html dir="rtl" lang="ar">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Basic Reader</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f0f0f0;
                            text-align: center;
                            padding: 50px;
                        }
                        .container {
                            background-color: white;
                            border-radius: 10px;
                            padding: 30px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            max-width: 800px;
                            margin: 0 auto;
                        }
                        h1 {
                            color: #6C5CE7;
                        }
                        .message {
                            margin: 20px 0;
                            color: #666;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Basic Server Running</h1>
                        <div class="message">
                            <p>This is a simple version of the application. We are currently facing an issue loading necessary libraries.</p>
                            <p>Please wait while we fix the issue.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html_content.encode('utf-8'))
                
        # معالجة ملفات static
        elif self.path.startswith('/static/'):
            file_path = self.path[8:]  # إزالة '/static/' من المسار
            full_path = os.path.join(STATIC_DIR, file_path)
            
            try:
                with open(full_path, 'rb') as file:
                    self.send_response(200)
                    
                    # تحديد نوع المحتوى بناءً على امتداد الملف
                    if full_path.endswith('.css'):
                        self.send_header('Content-type', 'text/css')
                    elif full_path.endswith('.js'):
                        self.send_header('Content-type', 'application/javascript')
                    elif full_path.endswith('.png'):
                        self.send_header('Content-type', 'image/png')
                    elif full_path.endswith('.jpg') or full_path.endswith('.jpeg'):
                        self.send_header('Content-type', 'image/jpeg')
                    else:
                        self.send_header('Content-type', 'application/octet-stream')
                    
                    self.end_headers()
                    self.wfile.write(file.read())
            except FileNotFoundError:
                self.send_error(404, "File not found")
                
        # معالجة المسارات الأخرى
        else:
            self.send_error(404, "Page not found")
    
    def log_message(self, format, *args):
        """
        تخصيص تنسيق رسائل السجل
        """
        logger.info(f"{self.address_string()} - {format % args}")

def run_server():
    """
    تشغيل الخادم على المنفذ المحدد
    """
    logger.info(f"بدء تشغيل الخادم البسيط على المنفذ {PORT}...")
    
    # استخدام التوجيه المحدد لمعالج الطلبات
    Handler = ArabicReaderHandler
    
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        logger.info(f"الخادم يستمع الآن على المنفذ {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("تم إيقاف الخادم بواسطة المستخدم")
        except Exception as e:
            logger.error(f"حدث خطأ غير متوقع: {e}")
        finally:
            httpd.server_close()
            logger.info("تم إغلاق الخادم")

if __name__ == "__main__":
    run_server()