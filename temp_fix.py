"""
ملف إصلاح مؤقت لإعادة تثبيت المكتبات المطلوبة لتطبيق القارئ العربي
"""
import os
import sys
import subprocess
import logging

# إعداد تسجيل السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# قائمة المكتبات المطلوبة
required_libraries = [
    "flask",
    "gunicorn",
    "PyPDF2",
    "pdfplumber", 
    "pillow", 
    "pytesseract"
]

def install_libraries():
    """
    تثبيت المكتبات المطلوبة باستخدام pip
    """
    logger.info("جاري تثبيت المكتبات المطلوبة...")
    
    for library in required_libraries:
        try:
            logger.info(f"تثبيت {library}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", library])
            logger.info(f"تم تثبيت {library} بنجاح.")
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل تثبيت {library}: {e}")
    
    logger.info("اكتمل تثبيت المكتبات.")

def check_libs():
    """
    التحقق من المكتبات المثبتة
    """
    logger.info("التحقق من المكتبات المثبتة:")
    
    for library in required_libraries:
        try:
            # محاولة استيراد المكتبة
            __import__(library.lower())
            logger.info(f"✓ {library} متوفرة")
        except ImportError:
            logger.warning(f"✗ {library} غير متوفرة")

def show_python_path():
    """
    عرض مسار البحث عن الحزم في Python
    """
    logger.info("مسارات البحث عن الحزم:")
    for path in sys.path:
        logger.info(f"- {path}")

if __name__ == "__main__":
    # عرض معلومات النظام
    logger.info(f"إصدار Python: {sys.version}")
    logger.info(f"المسار التنفيذي: {sys.executable}")
    
    # عرض المسارات
    show_python_path()
    
    # تثبيت المكتبات
    install_libraries()
    
    # التحقق من المكتبات المثبتة
    check_libs()
    
    # إنشاء ملف بسيط للتأكد من توفر pip
    try:
        with open("pip_check.txt", "w") as f:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
            f.write(result.stdout)
        logger.info("تم إنشاء ملف pip_check.txt")
    except Exception as e:
        logger.error(f"فشل إنشاء ملف pip_check.txt: {e}")