

# خطوات الإعداد المطلوبة بمجرد توفر VPS (IP + credentials)

هذا الملف قائمة تحقق (checklist) للخطوات اللي لازم تتعمل يدويًا **مرة واحدة بس**
لما الـ VPS يبقى جاهز. بعد كده، كل حاجة بتتم تلقائيًا عن طريق `.gitlab-ci.yml`.

الـ Runner هنا نوعه **Docker executor**: كل job بيشتغل جوه container معزول
بيتفتح ويتقفل تلقائيًا، مش بينفذ مباشرة على نظام السيرفر.

---

## 1. الدخول على السيرفر وتثبيت k3s

```bash
ssh root@<VPS_IP>

curl -sfL https://get.k3s.io | sh -

# تأكيد إنه شغال
sudo k3s kubectl get nodes
```

## 2. إعداد kubeconfig
ستخدم هذه الأوامر لتهيئـة أداة kubectl على جهازك لكي تتمكن من إدارة عنقود k3s بحسابك العادي ودون الحاجة لتنفيذ كل أمر باستخدام sudo.

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config
**mth1:export KUBECONFIG=~/.kube/config
**mth2:
- إضافة متغير البيئة KUBECONFIG بشكل دائم بحيث يعمل تلقائياً في كل مرة تفتح فيها جلسة Terminal جديد، قم بإضافته إلى ملف الإعدادات الخاص بالـ Shell (مثل ~/.bashrc).
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
تطبيق التغيير فوراً في النافذة الحالية دون الحاجة لإغلاقها وإعادة فتحها:
source ~/.bashrc

لتأكيد أن kubectl أصبحت تتصل بـ k3s بنجاح، نفذ الأمر التالي:

Bash:
kubectl cluster-info
```

تفصيل الأوامر:

mkdir -p ~/.kube: 
يُنشئ المجلد القياسي .kube داخل المجلد الرئيسي لمستخدمك لتخزين ملفات تهيئة كوبرنيتيس.

sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config: 
ينسخ ملف إعدادات k3s الافتراضي (الذي يتضمن مفاتيح الوصول للعنقود cluster) إلى المسار الذي تبحث فيه أداة kubectl تلقائيًا.

sudo chown $USER:$USER ~/.kube/config: 
يغير ملكية الملف المنسوخ من الجذر (root) إلى حسابك الحالي ($USER).

chmod 600 ~/.kube/config: 
يحدد صلاحيات قراءة وتعديل الملف للمالك فقط لضمان الأمان، حيث يرفض kubectl العمل إذا كانت صلاحيات ملف التهيئة مفتوحة لبقية مستخدمي النظام.

export KUBECONFIG=~/.kube/config: 
يضبط متغير البيئة KUBECONFIG في جلسة الطرفية (Terminal) الحالية ليشير صراحة إلى ملف التهيئة.

## 3. تثبيت Docker Engine على السيرفر

مطلوب لسببين: بناء واستيراد الصور لـ k3s (من مرحلة سابقة)، وأساسًا **لتشغيل
الـ Docker executor بتاع الـ Runner نفسه** - محتاج Docker Engine شغال على
الـ host عشان يقدر يفتح containers لكل job.

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

## 4. تجهيز نسخة من kubeconfig تقدر الـ containers توصلها
 لإعطاء (المستخدم الذي أنشأناه في Dockerfile ) الاتصال والتحكم بعنقود كوبرنيتيس (k3s)، ليتمكن من تنفيذ أوامر النشر (Deployment) وإدارة التطبيقات تلقائيًا أثناء تنفيذ خطوط الأنابيب (CI/CD Pipelines).

```bash
sudo mkdir -p /home/gitlab-runner
sudo cp ~/.kube/config /home/gitlab-runner/k3s-kubeconfig
sudo chown gitlab-runner:gitlab-runner /home/gitlab-runner/k3s-kubeconfig 2>/dev/null || true
```
(لو المستخدم `gitlab-runner` لسه مش موجود، هيتعمل تلقائيًا في الخطوة الجاية
لما تثبت الـ Runner - رجّع الأمر ده تاني بعدها لو فشل أول مرة)

## 5. تثبيت GitLab Runner على نفس السيرفر

```bash
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# ضيف مستخدم gitlab-runner لمجموعة docker عشان يقدر يستخدم الـ socket
sudo usermod -aG docker gitlab-runner
```

## 6. تسجيل الـ Runner (Docker executor)sudo usermod -aG docker gitlab-runner

من صفحة المشروع على GitLab: **Settings > CI/CD > Runners**
create project runner -> نضيف له tag 
، بعدين على ال vps:

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url https://gitlab.com/ \
  --token <authontication-TOKEN> \
  --executor docker \
  --docker-image alpine:3.20 \
  --docker-network-mode host \
  --docker-volumes /var/run/docker.sock:/var/run/docker.sock \
  --docker-volumes /home/gitlab-runner/k3s-kubeconfig:/kube/config:ro \
  --description "phosphor-snake-vps-runner"
```

نقط مهمة في الأمر ده:
- `--docker-network-mode host` 
عشان الـ containers تقدر توصل لـ k3s API على `127.0.0.1:6443` بالظبط زي ما لو كانت شغالة على السيرفر مباشرة
- `--docker-volumes /var/run/docker.sock:...` 
عشان مرحلة `build` تقدر تستخدم Docker engine بتاع السيرفر (من غير Docker-in-Docker أو `--privileged`)
- `--docker-volumes .../k3s-kubeconfig:/kube/config:ro` 
عشان مرحلة `deploy` تقدر توصل لملف الإعدادات؛ الملف ده هو نفسه الـ `KUBECONFIG` اللي متعرّف كمتغير في `.gitlab-ci.yml`
- --tag-list  "vps"
هذا لخيار لا نضعه لانه في GitLab الجديث عندما ننشىء ال authentication token يمنع استخدام هذا الخيار لان هذه الاعدادات تم تحديدها و حفظها بالفعل على خوادم GitLab اثناء انشائه.

## 7. إنشاء Deploy Token من GitLab (عشان الـ cluster يقدر يسحب الصور)

من صفحة المشروع: **Settings > Repository > Deploy tokens**
- Scope: `read_registry`
- خد الـ username والـ password اللي هيديهولك GitLab (يظهروا مرة واحدة بس)

بعدين على السيرفر:
```bash
kubectl create secret docker-registry gitlab-registry-secret \
  --docker-server=registry.gitlab.com \
  --docker-username=<DEPLOY_TOKEN_USERNAME> \
  --docker-password=<DEPLOY_TOKEN_PASSWORD> \

```

هذا الأمر يُستخدم في كوبرنيتيس (Kubernetes) لإنشاء **كائن سرّي (Secret)** يخزن بيانات الاعتماد الخاصة بربط العنقود (Cluster) بسجل حاويات خاص (Private Container Registry) على منصة GitLab.

**لماذا يُستخدم؟**
عندما تقوم بوضع صور الحاويات (Docker Images) الخاصة بمشروعك داخل سجل خاص غير متاح للعامة على GitLab، لن يتمكن كوبرنيتيس من سحب (Pull) تلك الصور وتشغيل الحاويات (Pods) بدون إذنيات. يُنشئ هذا الأمر المعتمدات المطلوبة حتى يستطيع كوبرنيتيس مصادقة حسابه لدى GitLab وسحب الصور بأمان.

---

**تفصيل أجزاء الأمر:**

* **`kubectl create secret docker-registry`**: 
يوجه كوبرنيتيس لإنشاء سر مخصص للتعامل مع سجلات Docker (من النوع `kubernetes.io/dockerconfigjson`).
* **`gitlab-registry-secret`**: 
اسم السر داخل العنقود (يمكنك تسميته بأي اسم يناسبك للاستدعاء لاحقاً).
* **`--docker-server=registry.gitlab.com`**: 
عنوان الخادم الخاص بسجل حاويات GitLab.
* **`--docker-username=<DEPLOY_TOKEN_USERNAME>`**: 
اسم المستخدم الخاص بتوكن النشر (Deploy Token) الذي أنشأته في مشروع GitLab.
* **`--docker-password=<DEPLOY_TOKEN_PASSWORD>`**: 
رمز السلسلة النصية الخاص بالـ Deploy Token (يقوم مقام كلمة المرور).

---

**كيف يُستخدم داخل ملفات التكوين (Deployment)؟**

بعد تشغيل الأمر، تقوم بالإشارة إلى اسم السر داخل ملف تعريف الـ Pod أو الـ Deployment عبر خيار `imagePullSecrets`:

```yaml
spec:
  containers:
  - name: my-app
    image: registry.gitlab.com/my-org/my-project/app:v1.0
  imagePullSecrets:
  - name: gitlab-registry-secret

```


## 8. تحديث أسماء الصور في الـ manifests

في `k8s/game-api-deployment.yaml` و `k8s/frontend-deployment.yaml`، غيّر:
```
registry.gitlab.com/YOUR-GROUP/YOUR-PROJECT/...
```
لمسار مشروعك الحقيقي على GitLab (تلاقيه في: Deploy > Container Registry).

## 9. التطبيق الأول اليدوي (bootstrap)

```bash
kubectl apply -f k8s/storageclass.yaml
kubectl apply -f k8s/redis-secret.yaml   
# عدّل الباسورد الأول، أو استخدم kubectl create secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/game-api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

## 10. توجيه الدومين/IP

عدّل `k8s/ingress.yaml` وحط الدومين الحقيقي بدل `snake.local` (أو سيبه لو هتستخدم IP مباشرة مع `/etc/hosts`).

---

## بعد كده بس

أي `git push` على `main` هيشغل تلقائيًا:
`test → build & push للـ Registry → deploy (kubectl set image) على الـ VPS`

كل مرحلة هتشتغل جوه container منعزل خاص بيها على نفس السيرفر - مفيش SSH،
ومفيش اعتماد على GitLab's shared runners.

-------------------------------------------------------------------------------------------------------------------------------
## DNS from (duckdns)
عملية إنشاء نطاق على DuckDNS وسريعة جداً ولا تتطلب سوى أقل من دقيقتين. 

 

1.تسجيل الدخول:متطلب أساسي. 

سجل الدخول عبر DuckDNS.org باستخدام حساب Google أو GitHub الخاص بك. 

 

2.حجز اسم النطاق:30 ثانية. 

في مربع sub-domain، أكتب الاسم الذي تريده لنطاقك (مثال: my-vps-server) ثم اضغط على add domain. 

 

3.ربط الـ IP:فوراً. 

سيظهر النطاق في القائمة تحت اسم my-vps-server.duckdns.org. ضع عنوان الـ IPv4 الخاص بالـ VPS في خانة الـ IP ثم اضغط update ip. 

 

4.حفظ الـ Token:مهم. 

انسخ رمز الـ Token الظاهر أعلى الصفحة، ستلاحظ أنه عبارة عن نص طويل من الأرقام والحروف وتصنع منه سكريبت التحديث التلقائي. 

 

تفعيل التحديث التلقائي للـ IP على VPS 

لضمان استمرار ربط النطاق بالـ VPS في حال تغير الـ IP: 

 

افتح مبدل الأوامر Terminal في الـ VPS وأنشئ مجلداً للخدمة: 

 

Bash 

mkdir -p ~/duckdns && cd ~/duckdns 
 

أنشئ ملف السكريبت: 

 

Bash 

nano duck.sh 
 

أضف السطر التالي (استبدل YOUR_DOMAIN باسم نطاقك بدون duckdns.org، و YOUR_TOKEN بالرمز الخاص بك): 

 

Bash 

echo url="https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=" | curl -k -K - 
 

احفظ الملف (Ctrl+O ثم Enter ثم Ctrl+X) وامنحه صلاحية التشغيل: 

 

Bash 

chmod 700 duck.sh 
 

اختبر السكريبت بتشغيله: 

 

Bash 

./duck.sh 
 

إذا ظهرت كلمة OK فإن الربط تم بنجاح. 

 

أضف السكريبت إلى crontab ليعمل كل 5 دقائق تلقائياً: 

 

Bash 

crontab -e 
 

أضف هذا السطر في الأسفل: 

Bash 

 15 3 15 * *  ~/duckdns/duck.sh >/dev/null 2>&1
سيحدث الip تلقائيا كل شهر يوم 15 الساعة 3 الدقيقة 15 دقيقة
-------------------------------------------------------------------------------------------------------------------------------
## tls/ssl certificate:
لتحويل الموقع إلى **`https://`** مجانًا وبشهادة رسمية موثوقة من **Let's Encrypt**، الحل القياسي والمعتمد في Kubernetes هو استخدام **`cert-manager`**.

يقوم `cert-manager` بإدارة عملية إصدار الشهادات وتجديدها تلقائيًا قبل انتهائها.

---

1. **تثبيت cert-manager على VPS:** الخطوة الأولى.
من داخل سيرفر الـ VPS، نفذ هذا الأمر لتثبيت أدوات وموارد `cert-manager`:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml

```

*(انتظر دقيقة لتشغيل الـ Pods الخاصة بـ cert-manager)*.


2. **إنشاء ClusterIssuer لـ Let's Encrypt:** الخطوة الثانية.
أنشئ ملفًا جديدًا باسم `k8s/cluster-issuer.yaml` داخل مشروعك. هذا الملف يخبر Let's Encrypt بكيفية التحقق من ملكيتك للدومين عبر HTTP-01 Challenge:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@gmail.com # <--- ضع إيميلك الحقيقي للتنبيهات
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            class: traefik

```
3. إنشاء ملف `k8s/redirect-middleware.yaml`
المشكلة المتبقية هي فقط أن **Traefik** يستقبل طلبات الـ HTTP ولا يعيد توجيهها تلقائياً إلى HTTPS.

لحل هذا الموضوع نهائياً وبطريقة مستقرة ومتوافقة مع K3s، سنتأكد من إعداد الـ Middleware الخاص بالتحويل بالشكل الصحيح:

تأكد من وجود هذا الملف داخل مجلد `k8s/` بالمحتوى التالي:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: redirect-to-https
spec:
  redirectScheme:
    scheme: https
    permanent: true

```
4. تحديث ملف `k8s/ingress.yaml`

عدّل ملف `k8s/ingress.yaml` ليربط الـ Entrypoints مع الـ Middleware بشكل صحيح:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: snake-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    # ربط الـ Middleware المسئول عن تحويل HTTP إلى HTTPS
    traefik.ingress.kubernetes.io/router.middlewares: default-redirect-to-https@kubernetescrd
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: traefik
  tls:
    - hosts:
        - snake-game.duckdns.org
      secretName: snake-game-tls
  rules:
    - host: snake-game.duckdns.org
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80

```

5. رفع التعديلات وتنفيذ الـ Pipeline

من جهازك المحلي، قم برفع الملفات للتطبيق تلقائياً:

```bash
git add k8s/redirect-middleware.yaml k8s/ingress.yaml
git commit -m "Configure HTTP to HTTPS redirect middleware"
git push origin main

```

5. **متابعة إصدار الشهادة:** التحقق.
يمكنك متابعة حالة طلب الشهادة من الـ VPS ببطء عبر هذا الأمر:

```bash
kubectl get certificate

```

*النتيجة الناجحة:* سترى حالة `READY` تحت القيمة `True` خلال دقيقة إلى دقيقتين. يمكنك بعدها زيارة `[https://snake-game.duckdns.org](https://snake-game.duckdns.org)` لتجد القفل الأخضر يعمل مجانًا ومؤمنًا بالكامل!



