"""
قارئ النصوص العربية - خادم بسيط
"""
import os
import http.server
import socketserver

# تحديد المنفذ
PORT = int(os.environ.get('PORT', 8080))

# تحديد الدليل الحالي
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class ArabicReaderHandler(http.server.SimpleHTTPRequestHandler):
    """معالج HTTP مخصص"""
    
    def __init__(self, *args, **kwargs):
        # تعيين دليل الخدمة إلى الدليل الحالي
        super().__init__(*args, directory=CURRENT_DIR, **kwargs)
    
    def translate_path(self, path):
        """ترجمة المسار للتعامل مع الملفات"""
        # التعامل مع المسار الرئيسي
        if path == '/' or path == '/index.html':
            return os.path.join(CURRENT_DIR, 'templates', 'index.html')
        
        # التعامل مع مسارات أخرى
        return super().translate_path(path)
    
    def log_message(self, format, *args):
        """تخصيص رسائل السجل"""
        print(f"{self.address_string()} - {format % args}")

def run_server():
    """تشغيل الخادم"""
    server_address = ('0.0.0.0', PORT)
    
    # استخدام ThreadingTCPServer للتعامل مع طلبات متعددة
    httpd = socketserver.ThreadingTCPServer(server_address, ArabicReaderHandler)
    
    print(f"بدء تشغيل خادم القارئ العربي على المنفذ {PORT}")
    print(f"يمكنك الوصول للتطبيق عبر: http://localhost:{PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nتم إيقاف الخادم")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()