

🎯 إجابات مركزة عن Nginx
📂 1. ما هي المسارات الثابتة وماذا يوجد بداخلها؟
📍 /usr/share/nginx/html:

ماذا يوجد بداخله؟ هذا هو المجلد الافتراضي في خادم Nginx لتخزين ملفات الموقع الثابتة (Static Files) مثل: index.html، ملفات CSS، ملفات JavaScript، والصور.  
غير معروف

في مشروعنا: تم نسخ ملف اللعبة index.html إليه مباشرة عبر الأمر COPY index.html /usr/share/nginx/html/index.html.  


📍 /etc/nginx/conf.d/default.conf:

ماذا يوجد بداخله؟ هذا هو المسار الذي يقرأ منه Nginx إعدادات المواقع (Server Blocks). تم نسخ ملف nginx.conf الخاص بنا ليحل محل الملف الافتراضي عبر الأمر COPY nginx.conf /etc/nginx/conf.d/default.conf.  


🔍 2. ما هو المتغير $uri ولماذا يبحث Nginx عن الملف ثم المجلد؟
💡 ما هو $uri أصلاً؟

هو متغير داخلي في Nginx يمثل المسار الذي كتبه المستخدم في المتصفح بعد اسم الدومين.

مثال: إذا طلب المستخدم http://localhost:8080/styles/main.css تكون قيمة $uri هي /styles/main.css.

⚙️ شرح الأمر try_files $uri $uri/ /index.html; بالترتيب:

  


الخطوة الأولى ($uri): يبحث Nginx في القرص الصلب: "هل يوجد ملف حقيقي بهذا الاسم بالضبط داخل /usr/share/nginx/html؟" إن وجده، يقوم بإرجاعه فوراً.  


الخطوة الثانية ($uri/): إن لم يجد ملفاً بهذا الاسم، يسأل: "هل يوجد مجلد بهذا الاسم؟" إن وجده، يحاول قراءة ملف الفهرس (index.html) من داخله.  


الخطوة الثالثة (/index.html): إن لم يجد لا ملفاً ولا مجلداً (مثلاً لو كتب المستخدم في المتصفح /game أو /profile)، يقوم بإعادة توجيه الطلب إلى /index.html.  


السبب: تطبيقات الواجهات الحديثة (SPA - Single Page Applications) تتكون من ملف index.html واحد فقط، والـ JavaScript هو من يدير التنقل والصفحات داخل المتصفح. هذا السطر يمنع ظهور خطأ 404 Not Found عند فتح أي رابط فرعي.  


🩺 3. لماذا أضفنا /healthz وأين توجد فعلياً؟
💡 لماذا أضفنا /healthz؟

يُستخدم كـ نقطة فحص السلامة (Health Check Endpoint). يقوم Docker أو Kubernetes بطلب هذا الرابط دورياً للتأكد من أن خادم Nginx يعمل ولم يتوقف.  
غير معروف


تم تعطيل السجلات فيه (access_log off;) لعدم ملء ملفات الـ Logs بآلاف الطلبات التلقائية بلا فائدة.  


📍 أين توجد فعلياً في النظام؟

لا توجد كملف أو مجلد على القرص الصلب إطلاقاً! ❌

هي نقطة افتراضية/وهمية (Virtual Endpoint) معرّفة فقط في الذاكرة داخل إعدادات Nginx. عندما يستلم Nginx أي طلب على الرابط /healthz يقوم بالرد مباشرة بحالة النجاح HTTP 200 وبنص "ok" دون قراءة أي ملف من القرص الصلب.  

#######################################################################################################



🛠️ الشرح الشامل لجميع الملفات والأوامر
🐳 1. ملف Docker Compose (docker-compose.yml)
YAML
services:
  redis:
    image: redis:7-alpine                       # [1]
    container_name: snake-redis                  # [2]
    restart: unless-stopped                     # [3]
    volumes:
      - redis_data:/data                        # [4]
    command: ["redis-server", "--appendonly", "yes"] # [5]
    healthcheck:                                # [6]
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - snake-net                               # [7]
      ***************************************************************************
image: redis:7-alpine:
استخدام صورة Redis الإصدار 7 المبنية على توزيعة Alpine الخفيفة جداً.  


container_name: snake-redis: 
تسمية الحاوية باسم ثابت بدلاً من اسم عشوائي.  


restart: unless-stopped: 
إعادة تشغيل الحاوية تلقائياً عند انهيارها أو عند إعادة تشغيل الجهاز.  

volumes: redis_data:/data:

المسار: ربط وحدة التخزين redis_data بالمجلد الداخلي /data.  


السبب: حفظ بيانات قاعدة البيانات بصفة دائمة على الجهاز المستضيف حتى لو حُذفت الحاوية.  

command: 
تشغيل خادم Redis مع خيار --appendonly yes لحفظ كل عملية كتابة على القرص ومنع فقدان البيانات.  

healthcheck: 
فحص جاهزية الخادم عن طريق إرسال أمر ping. الفحص يتم كل 5 ثوانٍ (interval: 5s)، بمهلة 3 ثوانٍ (timeout: 3s)، ويفشل بعد 5 محاولات خاطئة (retries: 5).  


networks: 
ربط الحاوية بشبكة معزولة تسمى snake-net.  
***************************************************************************

YAML
  game-api:
    build:
      context: ./backend                        # [1]
    container_name: snake-game-api
    restart: unless-stopped
    environment:                                # [2]
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      CORS_ORIGINS: "*"
    depends_on:
      redis:
        condition: service_healthy              # [3]
    healthcheck:                                # [4]
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/api/ready', timeout=2).status == 200 else sys.exit(1)"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 5s
    networks:
      - snake-net
    ports:
      - "8000:8000"                             # [5]
***************************************************************************
build: context: ./backend: 
المسار: مجلد ./backend المحتوي على كود Python وDockerfile. السبب: بناء صورة التطبيق الخلفي.  


environment: 
متغيرات البيئة لربط الخلفية بقاعدة بيانات Redis عبر اسم الحاوية redis والمنفذ 6379.  


depends_on ... service_healthy: 
تأجيل تشغيل الـ Backend حتى تصبح حاوية Redis جاهزة تماماً وتمر من اختبار السلامة.  


healthcheck: 
اختبار جاهزية التطبيق برمجياً بإرسال طلب لـ /api/ready بانتظار 5 ثوانٍ كفترة سماح أولية (start_period: 5s).  


ports: "8000:8000": المسار/الربط: 
ربط منفذ جهازك 8000 بـ منفذ الحاوية 8000 للوصول المباشر لـ API أثناء التطوير.  

***************************************************************************
YAML
  frontend:
    build:
      context: ./frontend                       # [1]
    container_name: snake-frontend
    restart: unless-stopped
    depends_on:
      game-api:
        condition: service_healthy              # [2]
    ports:
      - "8080:80"                               # [3]
    networks:
      - snake-net
build: context: ./frontend: 
المسار: مجلد ./frontend المحتوي على ملفات الواجهة الأمامية.  


depends_on: 
الانتظار حتى تكون خدمة الـ API جاهزة تماماً قبل تشغيل الواجهة.  


ports: "8080:80": المسار/الربط: 
ربط منفذ جهازك 8080 بـ منفذ الحاوية 80 (منفذ Nginx) لفتح اللعبة في المتصفح عبر http://localhost:8080. 
------------------------------------------------------------------------------------------------------------------------------


















🖼️ 2. ملف Dockerfile الخاص بالواجهة (frontend/Dockerfile)
Dockerfile
FROM nginx:1.27-alpine                         # [1]

RUN rm -f /etc/nginx/conf.d/default.conf /usr/share/nginx/html/* # [2]

COPY nginx.conf /etc/nginx/conf.d/default.conf # [3]
COPY index.html /usr/share/nginx/html/index.html # [4]

EXPOSE 80                                      # [5]

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/healthz || exit 1 # [6]

CMD ["nginx", "-g", "daemon off;"]              # [7]

***************************************************************************
FROM nginx:1.27-alpine: 
استخدام خادم Nginx النسخة الخفيفة المبنية على Alpine.  


RUN rm -f ...: 
حذف إعدادات Nginx الافتراضية والصفحات التجريبية لتنظيف الحاوية.  


COPY nginx.conf ...:  
نسخ إعداداتنا المحلية إلى /etc/nginx/conf.d/default.conf داخل الحاوية.  


COPY index.html ...:  
نسخ ملف الواجهة إلى /usr/share/nginx/html/index.html داخل الحاوية.  


EXPOSE 80: 
التنويه بأن الحاوية تستمع على المنفذ 80.  

HEALTHCHECK ...: 
فحص الخادم بطلب /healthz باستخدام أمر wget.  


الخيار -q: للعمل بصمت بدون طباعة تفاصيل التنزيل.  
غير معروف

الخيار -O-: لطباعة النتيجة في المخرجات مباشرة بدون حفظها في ملف.  


CMD ["nginx", "-g", "daemon off;"]: 
تشغيل Nginx في المقدمة (Foreground) لضمان عدم توقف الحاوية.  

-------------------------------------------------------------------------------------------------------------------------------














🐍 3. ملف Dockerfile الخاص بالخلفية (backend/Dockerfile)
Dockerfile
# ---------- المرحلة الأولى: تجميع المكتبات ----------
FROM python:3.12-slim AS builder                # [1]

WORKDIR /build                                  # [2]

ENV PIP_NO_CACHE_DIR=1 \                        # [3]
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .                         # [4]
RUN pip install --user --no-warn-script-location -r requirements.txt # [5]

# ---------- المرحلة الثانية: الصورة التشغيلية الخفيفة ----------
FROM python:3.12-slim                           # [6]

RUN useradd --create-home --shell /usr/sbin/nologin appuser # [7]

WORKDIR /app                                    # [8]

COPY --from=builder /root/.local /home/appuser/.local # [9]
COPY app/ ./app/                                # [10]

RUN chown -R appuser:appuser /app               # [11]
USER appuser                                    # [12]

ENV PATH=/home/appuser/.local/bin:$PATH \       # [13]
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/api/health', timeout=2).status == 200 else sys.exit(1)" # [14]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] # [15]

***************************************************************************
FROM python:3.12-slim AS builder: 
مرحلة بناء أولى لتثبيت المكتبات فقط.  


WORKDIR /build: 
تعيين المجلد /build كبيئة عمل.  


ENV PIP_NO_CACHE_DIR=1 ...: 
تعطيل كاش pip لتقليل حجم الصورة.  


COPY requirements.txt .: 
نسخ ملف المكتبات.  


RUN pip install --user ...: 
تثبيت المكتبات في مجلد خاص بالمستخدم (/root/.local).  


FROM python:3.12-slim: 
البدء من صورة جديدة تماماً لنقل المخرجات فقط بدون أدوات البناء الثقيلة.


RUN useradd ...: 
إنشاء مستخدم آمن باسم appuser بدون صلاحيات Root وبدون إمكانية تسجيل الدخول للـ Shell.  


WORKDIR /app: 
تعيين مجلد العمل الرئيسي إلى /app.  


COPY --from=builder ...:  
نقل المكتبات المثبتة فقط من المرحلة الأولى إلى المجلد الخص بـ appuser.  


COPY app/ ./app/:  
نقل كود البرمجة من ./app المحلي إلى /app/app/ للحاوية.  


RUN chown -R appuser:appuser /app: 
تغيير ملكية الملفات للمستخدم الجديد لحمايتها.  


USER appuser: 
تحويل مستخدم الحاوية ليكون appuser لزيادة الأمان.  


ENV PATH=...: 
إضافة المسار الخاص بمكتبات المستخدم إلى المتغير PATH ليعرف النظام مكان التشغيل.  


HEALTHCHECK: 
فحص صحة التطبيق عبر كود Python يطلب الرابط /api/health.  


CMD: 
تشغيل الخادم Uvicorn لتطبيق FastAPI على المنفذ 8000 والإنصات لجميع العناوين 0.0.0.0.  
-------------------------------------------------------------------------------------------------------------------------------








⚙️ 4. ملف إعدادات Nginx (nginx.conf)
Nginx
server {
    listen 80;                                  # [1]
    server_name _;

    root /usr/share/nginx/html;                 # [2]
    index index.html;                           # [3]

    # تقديم ملفات اللعبة والواجهة
    location / {                                # [4]
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # التوجيه العكسي للـ API
    location /api/ {                            # [5]
        proxy_pass http://game-api:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 3s;
        proxy_read_timeout 5s;
    }

    # نقطة فحص السلامة الوهمية
    location /healthz {                         # [6]
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
***************************************************************************
listen 80; server_name _; 
الاستماع على المنفذ 80 لكل أسماء النطاقات.  


root /usr/share/nginx/html; 
المسار: تحديد المجلد الذي يحتوي الملفات الثابتة للموقع.  


index index.html;
تحديد الصفحة الرئيسية الافتراضية.  


location /

try_files $uri $uri/ /index.html; 
البحث عن الملف ثم المجلد، ثم التوجيه لـ index.html في حال عدم وجودهما (لمنع أخطاء الـ SPA).  


add_header Cache-Control "no-cache";: منع المتصفح من كاش الملف لضمان تحميل التحديثات فوراً.  


location /api/:

proxy_pass http://game-api:8000/api/;: التوجيه: تحويل أي طلب يسمى /api/ تلقائياً إلى حاوية الـ Backend المسماة game-api عبر المنفذ 8000.  


السبب: إلغاء مشاكل حظر الاتصال بين نطاقين مختلفين (CORS) تماماً، لأن المتصفح سيتعامل مع منفذ واحد فقط.  


الترويسات (proxy_set_header): تمرير معطيات ورأس الطلب الحقيقي للعميل (مثل عنوان الـ IP الأصلي) إلى الـ Backend.  


location /healthz:

return 200 "ok\n"; 
إرجاع نص "ok" مع كود نجاح 200 فوراً من الذاكرة لجهات الفحص دون فتح أي ملف أو كتابة سجّلات


-------------------------------------------------------------------------------------------------------------------------------









5. (.gitlab-ci.yml)
لمتغيرات :  
BACKEND_IMAGE: $CI_REGISTRY_IMAGE/game-api: 
يعرّف مسار صورة الـ Backend داخل سجل GitLab الخاص بالمشروع.  
FRONTEND_IMAGE: $CI_REGISTRY_IMAGE/frontend: 
يعرّف مسار صورة الـ Frontend.  
KUBECONFIG: /kube/config: 
يحدد مسار ملف إعدادات الكوبرنيتس داخل الحاوية المؤقتة.  
مرحلة الاختبار (Stage 1: test)
- BACKEND_IMAGE: $CI_REGISTRY_IMAGE/game-api: 
يعرّف مسار صورة الـ Backend داخل سجل GitLab الخاص بالمشروع.  
- FRONTEND_IMAGE: $CI_REGISTRY_IMAGE/frontend: 
يعرّف مسار صورة الـ Frontend. 
- KUBECONFIG: /kube/config: 
يحدد مسار ملف إعدادات الكوبرنيتس داخل الحاوية المؤقتة.  
- rules: و - changes: و - backend/**/*: 
شروط التشغيل؛ تعمل هذه المهمة فقط إذا حدث تغيير في ملفات الـ backend.




#######################   #######################   #######################   #######################   #######################

#######################   #######################   #######################   #######################   #######################
rules: و - changes: و - backend/**/*                                         
- برمجياً، يعتمد هذا التركيب على آليات إدارة الأحداث (Event-Driven Pipeline) وتحليل الفوارق البرمجية (Git Diffing Engine) داخل منصة GitLab CI/CD.

1. rules: (قواعد التقييم المنطقي - Conditional Evaluation)
برمجياً:
- يمثل هذا المفتاح دالة شرطية (if/else statement) تنفذها بيئة GitLab قبل إنشاء المهمة (Job Creation Stage).  

2.changes: (محرك مقارنة الفوارق - Git Diff Engine)
برمجياً: يستدعي هذا الشرط محرك المقارنة الخاص بـ Git داخل المنصة لحساب الفوارق بين الإشارتين (Commit References):
Gitt Diff = Commit (new) \ Commit (old)
- طريقة العمل: ينظر النظام إلى قائمة الملفات التي تغيرت (سواء بالتعديل، الإضافة، أو الحذف) في عملية الرفع الأخيرة، ثم يقارن مسارات هذه الملفات بالتعبير النمطي (Pattern) المحدد تحته.

3. - backend/**/* (طابق المسارات بالتعبير النمطي - Glob Pattern Matching)
برمجياً: هذا النمط هو تعبير من نوع Glob Pattern يُستخدم لمطابقة مسارات الملفات والمجلدات:
backend/: يحدد مجلد البداية المستهدف (Root Directory).
**: يعني المطابقة الشاملة والعميقة عبر أي عدد من المجلدات الفرعية (Recursive Directory Matching)

/*: يعني المطابقة مع أي ملف بغض النظر عن اسمه أو امتداده (File Matching).

الفائدة البرمجية: منع استهلاك موارد سيرفر VPS في بناء واختبار الـ Backend عندما يكون التغيير المحذوف أو المعدل متعلقاً بمجلد الـ Frontend فقط، مما يرفع كفاءة وسرعة خط الإنتاج (CI/CD Pipeline Optimization).



#######################   #######################   #######################   #######################   #######################










مرحلة البناء (Stage 2: build)rules:
- rules: و - if: $CI_COMMIT_BRANCH == "main" 
تعمل فقط عند دمج أو رفع الكود على الفرع الرئيسي main.   
- docker build -t "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA" -t "$BACKEND_IMAGE:latest" ./backend 
بناء صورة الـ Backend ووسمها برقم الـ Commit ووسم latest.  
- docker push "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA" 
رفع الصورة برقم الـ Commit للسجل.  
- docker push "$BACKEND_IMAGE:latest"
رفع الصورة بوسم latest للسجل. 
- docker build -t "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA" -t "$FRONTEND_IMAGE:latest" ./frontend
بناء صورة الـ Frontend ووسمها بالوسمين.  
- docker push "$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA" 
رفع صورة الـ Frontend برقم الـ Commit.  
- docker push "$FRONTEND_IMAGE:latest"
رفع صورة الـ Frontend بوسم latest.

#######################   #######################   #######################   #######################   #######################

#######################   #######################   #######################   #######################   #######################

ملاحظة: 
وسم الصورة بوسمين (Tags) في هذا الأمر يرجع إلى أسلوب برمجي معتمد يُسمى Dual-Tagging Pattern في إدارة الحاويات وخطوط الإنتاج (CI/CD Pipelines).
إليك السبب والوظيفة البرمجية لكل وسم منهما:
1. الوسم الأول: $CI_COMMIT_SHORT_SHA (Immutaible / Versioned Tag)المفهوم: يمثل معرف التغيير الفريد الخاص بـ Git (مثال: a1b2c3d). 
السبب البرمجي:
#التتبع الدقيق (Traceability): يضمن لك معرفة الكود المصدري والدقيق الذي بُنيت منه هذه الصورة بالظبط.
#ثبات النسخ (Immutability): هذا الوسم فريد ولا يتكرر أبداً، مما يسمح بحفظ سجل كامل لجميع النسخ التاريخية في الـ Registry دون أن تطغى نسخة على أخرى. 
#الاسترجاع الآمن (Rollback): في مرحلة النشر deploy، يتصل كوبرنيتس بالصورة عبر هذا الوسم التزاماً بالنشر الآمن، وفي حال حدوث خطأ يمكنك الاسترجاع لوسم شفرة سابقة بسهولة.  
2. الوسم الثاني: latest (Mutable / Pointer Tag)المفهوم: يمثل مؤشراً متغيراً يشير دائماً إلى أحدث نسخة مستقرة تم بناؤها من الفرع الرئيسي. 
السبب البرمجي:
#سهولة السحب والتجربة (Developer Experience): يتيح لأي مطور أو خدمة أخرى سحب أحدث نسخة من الصورة محلياً عبر أمر بسيط مثل docker pull backend:latest دون الحاجة للبحث عن رقم الـ Commit SHA الخاص بها.
#تسهيل الإشارة: يعمل كعلامة مرجعية سريعة تشير دائماً إلى رأس خط الإنتاج (Head of Production)
الملخص:
بناء الصورة بالوسمين في أمر واحد:

Bash
docker build -t "$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA" -t "$BACKEND_IMAGE:latest" ./backend
يضمن لك الجمع بين الميزتين: توفير نسخة تاريخية محددة وثابتة لـ Kubernetes لمنع الأخطاء أثناء النشر الآلي، وفي نفس الوقت تحديث مؤشر latest ليعكس دائماً التعديل الأخير في السجل.

#######################   #######################   #######################   #######################   #######################




مرحلة النشر (Stage 3: deploy):

الأوامر الخاصة بالنشر:  
- kubectl set image deployment/game-api game-api="$BACKEND_IMAGE:$CI_COMMIT_SHORT_SHA"
أسلوب التحديث؛ 
تغيير صورة الـ Backend في كوبرنيتس بالصورة الجديدة برقم الـ Commit لضمان التحديث. 
- kubectl set image deployment/frontend frontend="$FRONTEND_IMAGE:$CI_COMMIT_SHORT_SHA" 
تغيير صورة الـ Frontend في كوبرنيتس. 
- kubectl rollout status deployment/game-api --timeout=120s
الانتظار لمدة أقصاها 120 ثانية للتأكد من نجاح تشغيل الـ Backend بدون أخطاء. 
- kubectl rollout status deployment/frontend --timeout=120s 
الانتظار والتأكد من نجاح تشغيل الـ Frontend. و environment: 
name: production: 
توثيق في منصة GitLab يوضح أن هذه العملية قامت بنشر التطبيق على بيئة الإنتاج الفعلية (Production).

-------------------------------------------------------------------------------------------------------------------------------






6. test files:
 المشروع يستخدم مكتبة **`pytest`** (وهي المكتبة الأشهر لاختبارات بايثون، وهذا واضح من أسماء الملفات):

### 1. ملف `pytest.ini` (ملف الإعدادات)

* **لماذا يُستخدم؟**
هو بمثابة "لوحة التحكم" لأداة الاختبار. بدلاً من كتابة إعدادات وأوامر طويلة في واجهة سطر الأوامر (Terminal) في كل مرة تريد فيها تشغيل الاختبارات، تقوم بحفظ هذه الإعدادات الثابتة في هذا الملف.
* **كيف يُستخدم؟**
يُوضع في المجلد الرئيسي للمشروع. تقوم بكتابة نصوص بسيطة بداخله لتحديد سلوك الاختبار، مثل:
* تحديد المجلد الذي يحتوي على الاختبارات (في حالتك هو مجلد `tests`).
* تفعيل إظهار تفاصيل الأخطاء بشكل موسع عند فشل الاختبار.
* تجاهل تحذيرات معينة (Warnings) لا تريد أن تظهر في النتائج.

---

### 2. ملف `conftest.py` (ملف التجهيزات المشتركة - Fixtures)

* **لماذا يُستخدم؟**
في البرمجة، غالباً ما تحتاج إلى "تجهيز" بيئة معينة قبل بدء الاختبار (مثلاً: فتح اتصال بقاعدة بيانات وهمية، أو تشغيل خادم محلي وهمي للتطبيق). ملف `conftest.py` يسمح لك بكتابة أكواد التجهيز هذه مرة واحدة فقط، ومشاركتها مع جميع ملفات الاختبار الأخرى دون الحاجة لعمل استيراد (Import) لها في كل مرة.
* **كيف يُستخدم؟**
تكتب بداخله دوال (Functions) مزودة بعلامة `@pytest.fixture`.
* **مثال عملي:** قد تكتب فيه دالة تُنشئ `TestClient` (عميل وهمي) يتصل بتطبيقك الموجود في `main.py`. بعد ذلك، أي ملف اختبار داخل مجلد `tests` سيتعرف تلقائياً على هذا "العميل الوهمي" ويستخدمه لاختبار التطبيق دون الحاجة لكتابة كود الاتصال من الصفر.

---

### 3. ملف `test_api.py` (ملف الاختبارات الفعلي)

* **لماذا يُستخدم؟**
هنا يُكتب كود الاختبار الحقيقي. حرف الـ `test_` في بداية اسم الملف ضروري جداً، لأن أداة `pytest` تبحث تلقائياً عن أي ملف يبدأ بهذا المقطع لتشغيله. هذا الملف مخصص لاختبار واجهات برمجة التطبيقات (API) الخاصة بمشروعك للتأكد من أنها تعمل كما هو متوقع.
* **كيف يُستخدم؟**
تقوم بكتابة دوال تبدأ أيضاً بـ `test_` (مثل `test_login_success`). داخل الدالة، تقوم بـ:
1. **إرسال طلب:** محاكاة طلب من مستخدم للـ API (مثلاً طلب POST برقم سري واسم مستخدم).
2. **التحقق (Assertion):** استخدام كلمة `assert` للتأكد من النتيجة. مثلاً، التحقق من أن حالة الاستجابة (Status Code) هي 200 (نجاح)، وأن التطبيق أعاد رسالة "تم تسجيل الدخول بنجاح".
----------------
#### يتم تنفيذ الاختبارات تلقائياً عبر موجه الأوامر (Terminal) باستخدام أداة `pytest` التي تتولى اكتشاف الملفات وتشغيلها وتقييم النتائج خطوة بخطوة.

**1. أمر التشغيل**
تقوم بفتح الـ Terminal داخل مجلد `backend` وتكتب الأمر التالي:

```bash
pytest

```

**2. مرحلة الاكتشاف (Test Discovery)**
بمجرد تشغيل الأمر، تقوم الأداة تلقائياً بـ:

* قراءة ملف `pytest.ini` لتطبيق الإعدادات العامة (مثل تحديد المجلد المستهدف `tests`).
* البحث داخل مجلد `tests` عن جميع الملفات التي يبدأ اسمها بـ `test_` (مثل `test_api.py`).
* دمج الإعدادات والـ Fixtures الموجودة في ملف `conftest.py`.
* البحث داخل الملفات عن أي دالة (Function) يبدأ اسمها بـ `test_`.

**3. مرحلة التجهيز والتنفيذ (Execution Lifecycle)**
عند تنفيذ كل دالة اختبار على حدة:

* **التجهيز (Setup):** تشغيل الـ Fixtures المحددة في `conftest.py` (مثلاً: إنشاء عميل وهمي `TestClient` للاتصال بالتطبيق).
* **إرسال الطلب:** تنفيذ الكود داخل دالة الاختبار (مثلاً: إرسال طلب `GET /` للتطبيق).
* **التحقق (Assertion):** فحص النتيجة باستخدام كلمة `assert` (مثلاً: التأكد من أن رمز الاستجابة هو `200 OK`).
* **التنظيف (Teardown):** إغلاق الاتصالات أو حذف البيانات المؤقتة إن وجدت.

**4. إظهار النتائج (Test Report)**
تطبع `pytest` النتيجة في الـ Terminal على النحو التالي:

* **رمز `.` (نقطة):** يعني أن الاختبار مر بنجاح (Passed).
* **حرف `F`:** يعني أن الاختبار فشل (Failed)، وستعرض لك الأداة السطر المحدد الذي حدث فيه الخطأ وسبب الفشل.
* **ملخص نهائي:** يوضح عدد الاختبارات وتفاصيل زمن التنفيذ (مثال: `1 passed in 0.12s`).

-------------------------------------------------------------------------------------------------------------------------------









