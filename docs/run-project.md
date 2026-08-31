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

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG=~/.kube/config
```

## 3. تثبيت Docker Engine على السيرفر

مطلوب لسببين: بناء واستيراد الصور لـ k3s (من مرحلة سابقة)، وأساسًا **لتشغيل
الـ Docker executor بتاع الـ Runner نفسه** - محتاج Docker Engine شغال على
الـ host عشان يقدر يفتح containers لكل job.

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

## 4. تجهيز نسخة من kubeconfig تقدر الـ containers توصلها

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

## 6. تسجيل الـ Runner (Docker executor)

من صفحة المشروع على GitLab: **Settings > CI/CD > Runners** وهات الـ registration token، بعدين:

```bash
sudo gitlab-runner register \
  --non-interactive \
  --url https://gitlab.com/ \
  --registration-token <TOKEN> \
  --executor docker \
  --docker-image alpine:3.20 \
  --docker-network-mode host \
  --docker-volumes /var/run/docker.sock:/var/run/docker.sock \
  --docker-volumes /home/gitlab-runner/k3s-kubeconfig:/kube/config:ro \
  --tag-list "vps" \
  --description "phosphor-snake-vps-runner"
```

نقط مهمة في الأمر ده:
- `--docker-network-mode host` عشان الـ containers تقدر توصل لـ k3s API على `127.0.0.1:6443` بالظبط زي ما لو كانت شغالة على السيرفر مباشرة
- `--docker-volumes /var/run/docker.sock:...` عشان مرحلة `build` تقدر تستخدم Docker engine بتاع السيرفر (من غير Docker-in-Docker أو `--privileged`)
- `--docker-volumes .../k3s-kubeconfig:/kube/config:ro` عشان مرحلة `deploy` تقدر توصل لملف الإعدادات؛ الملف ده هو نفسه الـ `KUBECONFIG` اللي متعرّف كمتغير في `.gitlab-ci.yml`
- الـ tag **لازم يكون `vps`** بالظبط، لأن `.gitlab-ci.yml` بيدور على runner بالتاج ده في كل المراحل

## 7. إنشاء Deploy Token من GitLab (عشان الـ cluster يقدر يسحب الصور)

من صفحة المشروع: **Settings > Repository > Deploy tokens**
- Scope: `read_registry`
- خد الـ username والـ password اللي هيديهولك GitLab (يظهروا مرة واحدة بس)

بعدين على السيرفر:
```bash
kubectl create secret docker-registry gitlab-registry-secret \
  --docker-server=registry.gitlab.com \
  --docker-username=<DEPLOY_TOKEN_USERNAME> \
  --docker-password=<DEPLOY_TOKEN_PASSWORD>
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
kubectl apply -f k8s/redis-secret.yaml   # عدّل الباسورد الأول، أو استخدم kubectl create secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml
kubectl apply -f k8s/game-api-deployment.yaml
kubectl apply -f k8s/game-api-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
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
