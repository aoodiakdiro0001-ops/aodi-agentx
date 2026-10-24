# Aodı-AgentX

**Multi-Agent Distributed AI Operations Framework — فريق وكلاء ذكاء اصطناعي موزّع يعمل على عتادك بالكامل، بلا اشتراك سحابي واحد.**

فريق رباعي من الوكلاء: **استطلاع** يقرأ هيكل المشروع، **تدقيق** يصطاد الثغرات، **اختبارات** يكتب pytest، **تكامل** يلخص المطلوب من المطور — كلهم عبر Ollama على أجهزتك (Mac / Windows / Linux)، والمنسق يوزع الدفعات على كل عقدة صحية بالتوازي مع فشل سلس تلقائي.

- **License:** MIT © 2026 Baran Avisat
- **Support:** baranavisat@gmail.com · WhatsApp +90 531 326 37 22 (wa.me/905313263722)
- **100% free stack:** Ollama · SQLite/JSON · GitHub Actions · (اختياري: Tailscale, Sepolia testnet)
- **الخط:** Aodı Akdıro Suite — github.com/aoodiakdiro0001-ops

## ماذا يفعل فوراً؟

| أمر واحد | ما يحدث فعلاً |
|---|---|
| `aodi-agentx init` | يكتشف عقد Ollama، يفحصها متوازياً، ويطبع الحالة والزمن |
| `add-node win https://tunnel.lhr.life` | يربط خادم ذكاء ثانياً عبر أي رابط HTTP (Tailscale أو نفق) |
| `run code_audit --path ./app` | تدقيق أمني: 10 قواعد ساكنة + وكلاء بالتوازي عبر العقد + دمج + تقرير |
| `run test_gen --path ./app --target svc.py` | يكتب ملف pytest جاهزاً في `generated_tests/` |
| `run custom "اشرح بنية المشروع"` | مهمة حرة عبر أقرب وكيل |
| `dashboard/` | لوحة عربية RTL: صحة العقد، تشغيل المهام، تقارير |

## المعمارية — لماذا أربع لغات؟

```
 [ aodi-agentx CLI (Node) ]   [ dashboard (HTML/JS) ]
              \                    /
        [ core API — Orchestrator (Python stdlib / FastAPI اختياري) ]
                    |                |
   [ netmgr — Go: منافذ وموارد بـ goroutines ]   [ Ollama nodes × N ]
                                                    (Mac · Windows · …)
                    |
        [ contracts (Solidity) — تثبيت بصمات sha256 على testnet (اختياري) ]
```

- **Python (core):** تنظيم مهام الوكلاء، تقسيم الدفعات، تحويل عقدة فاشلة إلى صحيحة، مهام بالخيوط.
- **Go (netmgr):** فحص حتى 3000 منفذ بـ200 goroutine، وموارد النظام، وprobe للروابط — بلا تبعيات.
- **Node (CLI):** صفر تبعيات npm — أوامر عربية واضحة وملف ترميز محلي.
- **Solidity (اختياري):** registry للبصمات: من سجّل وماذا ومتى.

## البدء في دقيقة (بلا pip وبلا npm)

```bash
git clone https://github.com/aoodiakdiro0001-ops/aodi-agentx && cd aodi-agentx

# 1) core (Python 3.8+ فقط):
python3 core/server.py --port 8787

# 2) طرف آخر — CLI (Node 18+ فقط):
cd cli && node index.js doctor
node index.js add-node mac http://127.0.0.1:11434
node index.js add-node win https://your-tunnel.lhr.life
node index.js run code_audit --path ../examples

# 3) اللوحة:
open http://127.0.0.1:8787/dashboard
```

اختياري: `pip install fastapi uvicorn` ثم `python3 core/server.py --engine fastapi` — وnetmgr: داخل `netmgr/` نفّذ `go build -o agentx-netmgr .` ثم `./agentx-netmgr` (GET `/ports?host=127.0.0.1&from=1&to=1024`).

## الضمانات

- الوضع الأساسي صفر تبعيات خارجية: `urllib` + `http.server` + `threading`.
- فشل سلس: عقدة سقطت؟ تُنقل دفعتها تلقائياً إلى العقدة التالية الصحيحة.
- تدقيق حقيقي متعدد اللغات: Python / JS / Go / Java / SQL / YAML / Solidity.
- 6 اختبارات وحدة بلا شبكة: `python3 tests/test_scanner.py` — وCI مجانية على GitHub Actions.
- حدود تشغيل واضحة: مهلة الطلب `AODX_TIMEOUT` (180 ثانية افتراضاً) وحد الملف 100KB.

## خريطة المسار

- قواعد إضافية لمحللات Solidity وGo وJava (10 قواعد الآن).
- إخراج SARIF لدمج GitHub Code Scanning.
- watch في netmgr للإفراغ التلقائي والتنبيهات.
- طبق عقود: نشر AgentXProof على Sepolia بأمر واحد.

## Honest disclosure

- هذه أداة مساعدة لا بديل عن قراءة المطور: القواعد الساكنة سريعة وقد تعطي إنذارات خاطئة، والتقرير النهائي قرار إنساني.
- وحدة العقود اختيارية 100% — أطفئها وستشتغل كل الوظائف الأساسية بدونهما.
- لا يوجد أي اتصال سحابي: كل التوليد عبر عقد Ollama التي سجّلتها أنت.

© 2026 Baran Avisat · MIT License · BTC `bc1q8dhtdrndxsl70e97t8grydfe6pjue37zrhzf6c` · USDT-TRC20 `TLWdTjqqogkXNEXGiPWsGdjFP6ioycxeWW`
