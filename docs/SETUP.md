# SETUP — Aodı-AgentX

## المتطلبات
- Python 3.8+ (بدون pip إطلاقاً) — أو مع pip لو تريد وضع FastAPI
- Node 18+ (للـ CLI) — بلا npm install
- Go 1.21+ (اختياري لـ netmgr)

## تثبيت وتشغيل (5 أوامر)

```bash
python3 core/server.py --port 8787          # ثمратив core
cd cli && node index.js init                # فحص العقد
node index.js add-node mac http://127.0.0.1:11434
node index.js run code_audit --path ../examples
open http://127.0.0.1:8787/dashboard
```

## إعداد جهاز ثانٍ (Windows مثال حي)

1. على الجهاز الثاني: ثبّت Ollama ثم `ollama pull qwen2.5-coder`
2. انشر الخدمة خارجياً: `OLLAMA_HOST=0.0.0.0 ollama serve` — أو نفق آمن: `ssh -R 80:localhost:11434 nokey@localhost.run` وسيطبع رابط https
3. من الجهاز الأول: `node index.js add-node win https:// ر-link .lhr.life`

أو (الأفضل على المدى البعيد): **Tailscale** على كل جهاز بحساب واحد ثم `add-node win http://100.x.y.z:11434`

## متغيرات البيئة

| المتغير | الافتراضي | الوصف |
|---|---|---|
| `AODX_API` | http://127.0.0.1:8787 | رابط core للـCLI |
| `AODX_PORT` | 8787 | منفذ core |
| `AODX_TIMEOUT` | 180 | مهلة توليد كل وكيل (ثانية) |
| `AODIX_HOME` | ~/.aodix | مجلد الحالة (nodes.json + tasks.jsonl) |
| `NETMGR_ADDR` | :7231 منفذ netmgr |

## فحص صحة

```bash
python3 tests/test_scanner.py -v   # 6 اختبارات بلا شبكة
node --check cli/index.js
cd netmgr && go vet ./... && go build ./.
```
