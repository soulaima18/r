/**
 * قارئ النصوص العربية - ملف السكريبت الرئيسي
 */

// المتغيرات العامة
let pages = [''];
let currentPageIndex = 0;
let isPlaying = false;
let speech = null;
let currentChunks = [];
let currentChunkIndex = 0;
let arabicVoice = null;

// التهيئة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', init);

// تهيئة التطبيق
function init() {
    // عناصر DOM
    const textInput = document.getElementById('textInput');
    const fileInput = document.getElementById('fileInput');
    const browseButton = document.getElementById('browseButton');
    const uploadArea = document.getElementById('uploadArea');
    const processButton = document.getElementById('processButton');
    const outputContent = document.getElementById('outputContent');
    const playButton = document.getElementById('playButton');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const speedControl = document.getElementById('speedControl');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const currentPageDisplay = document.getElementById('currentPage');
    const themeToggle = document.getElementById('themeToggle');

    // تعيين مستمعي الأحداث
    setupEventListeners();
    
    // تهيئة تخليق الكلام
    initSpeechSynthesis();
    
    // التحقق من السمة المحفوظة
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
    
    // وظائف الإعداد
    
    // إعداد مستمعي الأحداث
    function setupEventListeners() {
        browseButton.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileUpload);
        processButton.addEventListener('click', processText);
        playButton.addEventListener('click', togglePlayPause);
        prevButton.addEventListener('click', goToPrevPage);
        nextButton.addEventListener('click', goToNextPage);
        speedControl.addEventListener('change', updateSpeed);
        themeToggle.addEventListener('click', toggleTheme);
        
        // إعداد السحب والإفلات
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('active');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('active');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('active');
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFileUpload();
            }
        });
    }
    
    // تهيئة تخليق الكلام
    function initSpeechSynthesis() {
        speech = new SpeechSynthesisUtterance();
        speech.lang = 'ar';
        
        speech.onend = handleSpeechEnd;
        
        // الحصول على الأصوات المتاحة عند تحميلها
        window.speechSynthesis.onvoiceschanged = () => {
            const voices = window.speechSynthesis.getVoices();
            arabicVoice = selectBestVoiceForArabic(voices);
            
            if (arabicVoice) {
                console.log(`الصوت المختار: ${arabicVoice.name} (${arabicVoice.lang})`);
                speech.voice = arabicVoice;
            } else {
                console.log('لم يتم العثور على صوت عربي، استخدام الصوت الافتراضي');
            }
        };
        
        // محاولة أولية للحصول على الأصوات
        if (window.speechSynthesis.getVoices().length > 0) {
            const voices = window.speechSynthesis.getVoices();
            arabicVoice = selectBestVoiceForArabic(voices);
            if (arabicVoice) speech.voice = arabicVoice;
        }
    }
    
    // اختيار أفضل صوت للعربية
    function selectBestVoiceForArabic(voices) {
        // المحاولة الأولى: البحث عن صوت بلغة 'ar-SA'
        let voice = voices.find(v => v.lang === 'ar-SA');
        
        // المحاولة الثانية: البحث عن أي لغة عربية
        if (!voice) {
            voice = voices.find(v => v.lang.startsWith('ar'));
        }
        
        // المحاولة الثالثة: البحث عن صوت باسم عربي
        if (!voice) {
            voice = voices.find(v => 
                v.name.toLowerCase().includes('arab') || 
                v.name.toLowerCase().includes('اَلْعَرَبِيَّةُ') ||
                v.name.toLowerCase().includes('العربية')
            );
        }
        
        return voice;
    }
    
    // معالجة تحميل الملف
    function handleFileUpload() {
        const file = fileInput.files[0];
        if (!file) return;
        
        // للبساطة في هذا المثال، سنتعامل فقط مع ملفات .txt
        // في تطبيق كامل، سنحتاج إلى التعامل مع ملفات PDF بشكل مختلف
        const fileName = file.name.toLowerCase();
        
        if (fileName.endsWith('.txt') || fileName.endsWith('.text')) {
            loadingIndicator.style.display = 'block';
            
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const content = e.target.result;
                textInput.value = content;
                processText();
                loadingIndicator.style.display = 'none';
            };
            
            reader.onerror = () => {
                alert('حدث خطأ أثناء قراءة الملف');
                loadingIndicator.style.display = 'none';
            };
            
            reader.readAsText(file);
        } else if (fileName.endsWith('.pdf')) {
            alert('تنويه: معالجة ملفات PDF تتم عادة على الخادم، في هذه النسخة يمكنك فقط معالجة الملفات النصية أو إدخال النص مباشرة');
            loadingIndicator.style.display = 'none';
        } else {
            alert('الرجاء تحميل ملف بتنسيق PDF أو نص فقط');
        }
    }
    
    // معالجة النص المدخل
    function processText() {
        const text = textInput.value.trim();
        if (!text) {
            alert('الرجاء إدخال نص أو تحميل ملف');
            return;
        }
        
        // معالجة بسيطة: تقسيم بواسطة الأسطر الفارغة لإنشاء صفحات
        pages = text.split(/\n\s*\n/).filter(page => page.trim().length > 0);
        
        if (pages.length === 0) {
            pages = [text]; // إذا لم تكن هناك أسطر فارغة، تعامل معها كصفحة واحدة
        }
        
        // إعادة التعيين إلى الصفحة الأولى
        currentPageIndex = 0;
        updatePageDisplay();
        
        // تفعيل عناصر التحكم
        enableControls();
    }
    
    // تحديث عرض الصفحة
    function updatePageDisplay() {
        if (pages.length === 0) {
            outputContent.innerHTML = '';
            currentPageDisplay.textContent = 'لا يوجد محتوى';
            return;
        }
        
        const pageContent = pages[currentPageIndex];
        
        // تنسيق مع فواصل الفقرات
        const formattedContent = pageContent
            .split('\n')
            .map(line => line.trim() ? `<p>${line}</p>` : '')
            .join('');
        
        outputContent.innerHTML = formattedContent;
        currentPageDisplay.textContent = `الصفحة ${currentPageIndex + 1} من ${pages.length}`;
        
        // الإعداد للقراءة
        prepareForReading();
    }
    
    // تفعيل عناصر التحكم
    function enableControls() {
        playButton.disabled = false;
        prevButton.disabled = currentPageIndex <= 0;
        nextButton.disabled = currentPageIndex >= pages.length - 1;
    }
    
    // تعطيل عناصر التحكم
    function disableControls() {
        playButton.disabled = true;
        prevButton.disabled = true;
        nextButton.disabled = true;
    }
    
    // الانتقال إلى الصفحة السابقة
    function goToPrevPage() {
        if (currentPageIndex > 0) {
            // إيقاف أي كلام جاري
            if (isPlaying) {
                stopSpeech();
            }
            
            currentPageIndex--;
            updatePageDisplay();
            enableControls();
        }
    }
    
    // الانتقال إلى الصفحة التالية
    function goToNextPage() {
        if (currentPageIndex < pages.length - 1) {
            // إيقاف أي كلام جاري
            if (isPlaying) {
                stopSpeech();
            }
            
            currentPageIndex++;
            updatePageDisplay();
            enableControls();
        }
    }
    
    // تبديل التشغيل/الإيقاف المؤقت
    function togglePlayPause() {
        if (isPlaying) {
            pauseSpeech();
        } else {
            startReading();
        }
        
        updatePlayButtonState();
    }
    
    // تحديث حالة زر التشغيل
    function updatePlayButtonState() {
        playButton.textContent = isPlaying ? 'إيقاف القراءة' : 'بدء القراءة';
    }
    
    // بدء القراءة
    function startReading() {
        // إلغاء أي كلام جاري
        window.speechSynthesis.cancel();
        
        // التحقق من وجود محتوى للقراءة
        if (pages.length === 0 || !pages[currentPageIndex]) {
            return;
        }
        
        isPlaying = true;
        
        // إعداد مقاطع النص للقراءة بسلاسة
        prepareForReading();
        
        // بدء التحدث بالمقطع الأول
        speakCurrentChunk();
    }
    
    // الإعداد للقراءة
    function prepareForReading() {
        if (!pages[currentPageIndex]) return;
        
        // تقسيم النص إلى مقاطع يمكن إدارتها لأداء أفضل للكلام
        const pageText = pages[currentPageIndex].replace(/\n/g, ' ');
        currentChunks = splitTextIntoChunks(pageText);
        currentChunkIndex = 0;
    }
    
    // تقسيم النص إلى مقاطع
    function splitTextIntoChunks(text) {
        // أولاً، قسم بواسطة محددات الجملة
        const sentences = text.split(/([.!?،؛؟])/);
        
        // إعادة دمج الجمل مع محدداتها
        const fullSentences = [];
        for (let i = 0; i < sentences.length - 1; i += 2) {
            fullSentences.push(sentences[i] + (sentences[i+1] || ''));
        }
        
        // إذا كان هناك عنصر فردي متبقي، أضفه
        if (sentences.length % 2 !== 0) {
            fullSentences.push(sentences[sentences.length - 1]);
        }
        
        // الآن، قم بتجميع الجمل في مقاطع
        const chunks = [];
        let currentChunk = '';
        
        for (const sentence of fullSentences) {
            if (sentence.trim().length === 0) continue;
            
            if (currentChunk.length + sentence.length < 200) {
                currentChunk += sentence + ' ';
            } else {
                if (currentChunk.trim()) {
                    chunks.push(currentChunk.trim());
                }
                currentChunk = sentence + ' ';
            }
        }
        
        // أضف المقطع الأخير إذا لم يكن فارغًا
        if (currentChunk.trim()) {
            chunks.push(currentChunk.trim());
        }
        
        return chunks;
    }
    
    // التحدث بالمقطع الحالي
    function speakCurrentChunk() {
        if (currentChunkIndex < currentChunks.length) {
            const chunk = currentChunks[currentChunkIndex];
            
            speech.text = chunk;
            speech.rate = parseFloat(speedControl.value);
            
            // حاول دائمًا استخدام الصوت العربي إذا كان متاحًا
            if (arabicVoice) {
                speech.voice = arabicVoice;
            }
            
            window.speechSynthesis.speak(speech);
            
            // تسليط الضوء على النص الحالي الذي تتم قراءته (مبسط)
            highlightCurrentChunk(chunk);
        } else {
            // وصلنا إلى نهاية جميع المقاطع
            isPlaying = false;
            updatePlayButtonState();
            
            // إذا كان التقدم التلقائي مفعلاً وهناك المزيد من الصفحات
            if (currentPageIndex < pages.length - 1) {
                goToNextPage();
                // خيار: بدء قراءة الصفحة التالية تلقائيًا
                // setTimeout(startReading, 1000);
            }
        }
    }
    
    // تسليط الضوء على النص الذي تتم قراءته
    function highlightCurrentChunk(chunk) {
        // تنفيذ بسيط - عرض أول بضع كلمات من المقطع فقط
        const previewText = chunk.split(' ').slice(0, 3).join(' ') + '...';
        console.log(`قراءة: ${previewText}`);
        
        // تنفيذ أكثر تقدمًا سيبحث عن النص ويسلط الضوء عليه في DOM
    }
    
    // معالجة حدث انتهاء الكلام
    function handleSpeechEnd() {
        currentChunkIndex++;
        
        if (isPlaying) {
            speakCurrentChunk();
        }
    }
    
    // إيقاف الكلام مؤقتًا
    function pauseSpeech() {
        isPlaying = false;
        window.speechSynthesis.cancel();
    }
    
    // إيقاف الكلام
    function stopSpeech() {
        isPlaying = false;
        window.speechSynthesis.cancel();
        updatePlayButtonState();
    }
    
    // تحديث معدل الكلام
    function updateSpeed() {
        speech.rate = parseFloat(speedControl.value);
        
        // إذا كان يتحدث حاليًا، أعد التشغيل بالمعدل الجديد
        if (isPlaying) {
            window.speechSynthesis.cancel();
            speakCurrentChunk();
        }
    }
    
    // التبديل بين السمة الفاتحة والداكنة
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }
}