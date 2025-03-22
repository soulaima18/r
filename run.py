"""
تشغيل تطبيق الويب لقارئ النصوص العربية مباشرة بواسطة خادم Flask الافتراضي
تم تعديله لاستخدام تطبيق بسيط في حالة عدم تمكن من استيراد التطبيق الرئيسي
"""

import os
import sys
import logging

# إعداد تسجيل السجلات للتصحيح
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # محاولة استيراد التطبيق مباشرة
        logger.info("بدء تحميل التطبيق...")
        from app import app
        
        # تشغيل التطبيق على المنفذ 5000
        logger.info("بدء تشغيل التطبيق على المنفذ 5000...")
        app.run(host="0.0.0.0", port=5000, debug=True)
        
    except ImportError as e:
        logger.error(f"فشل استيراد التطبيق: {e}")
        logger.info("إنشاء تطبيق بسيط للتجربة...")
        
        try:
            # إنشاء تطبيق بسيط في حالة فشل استيراد app.py
            from flask import Flask, render_template, send_from_directory
            
            simple_app = Flask(__name__)
            
            @simple_app.route('/')
            def index():
                return render_template('index.html')
                
            @simple_app.route('/static/<path:path>')
            def send_static(path):
                return send_from_directory('static', path)
            
            logger.info("بدء تشغيل التطبيق البسيط على المنفذ 5000...")
            simple_app.run(host="0.0.0.0", port=5000, debug=True)
            
        except ImportError as flask_error:
            logger.error(f"فشل استيراد Flask: {flask_error}")
            print("Flask غير مثبتة. جاري إنشاء خادم HTTP بسيط...")
            
            # إنشاء خادم HTTP بسيط باستخدام http.server
            import http.server
            import socketserver
            
            PORT = 5000
            
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/':
                        self.path = '/templates/index.html'
                    return http.server.SimpleHTTPRequestHandler.do_GET(self)
            
            with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
                print(f"خادم HTTP يعمل على المنفذ {PORT}")
                httpd.serve_forever()
        
    except Exception as general_error:
        logger.error(f"حدث خطأ غير متوقع: {general_error}")
        sys.exit(1)