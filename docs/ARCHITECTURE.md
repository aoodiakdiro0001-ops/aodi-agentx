# ARCHITECTURE — Aodı-AgentX v1.0.0

## المكونات

| المكوين | اللغة | الدور | التبعيات |
|---|---|---|---|
| `core/` | Python 3.8+ | API + Orchestrator + scanner + agents | صفر (stdlib) · FastAPI اختياري |
| `netmgr/` | Go 1.21+ | فحص منافذ متوازٍ + موارد + probe | صفر (stdlib) |
| `cli/` | Node 18+ | أداة سطر الأوامر | صفر (npm) |
| `dashboard/` | HTML/JS | لوحة عربية RTL | صفر |
| `contracts/` | Solidity | تسجيل بصمات sha256 | ethers (اختياري) |

## تدفق مهمة code_audit

```
CLI/لوحة → POST /api/tasks → new_task(thread)
   → collect_files(مسار)                [استبعاد .git/node_modules/venv/…]
   → static_findings                     [10 قواعد regex عبر ThreadPool(8)]
   → _file_batches(3.5KB لدفعة)
   → generate_many(دفعات, roundrobin عقد)   ← Ollama /api/generate (stream:false)
   → parse findings JSON لكل دفعة
   → دمج (إزالة المكرر حسب file+line)
   → تقرير: severity/map/agents/latency
```

## خصائص التحمل

- **فشل سلس**: `generate()` يجرب العقد بالترتيب (الصحيح أولاً). أي 500/timeout ينتقل للعقدة التالية.
- **توازي حقيقي**: `generate_many` بنفذ خيوط الوضع 4؛ كل دفعة لعقدة مختلفة عند وجود أكثر من عقدة.
- **صحة العقد**: فحص متوازٍ بن `/api/tags` مهلة 8 ثوان؛ مخزن في ذاكرة العملية.
- **حدود**: ملف ≤ 100KB · دفعة ≤ 3.5K حرف · منافذ ≤ 3000 لكل فحص netmgr.

## القرارات التصميمية

- **لا LangChain/LlamaIndex**: قناة Ollama HTTP مباشرة تكفي = تبعيات أقل، للصيانة أسهل، وللاستخدام الأسرع.
- **قواعد ساكنة + وكلاء**: الأدوات الآلية حاكمة سريعة؛ الودجت يفترس الإيجابيات الخاطئة ويضيف ما تخفى.
- **stdlib-first**: الخدمة تعمل في أي بيئة بايثون 3.8+ من أول ثانية (حتى بلا pip). غلاف FastAPI متوفر لمن يريده.
- **السجل في JSONL**: `~/.aodix/tasks.jsonl` — تدقيق لاحق لكل مهمة بلا قاعدة بيانات.

## التطوير المستقبلي (خارطة)

v1.1: قواعد Solidity/JS-frame · SARIF output · مهمة PR-fixer (تطبيق الإصلاحات فعلياً في فروع git)
v1.2: netmgr watchdog + قياس GPU عبر Ollama /api/ps · واجهة الويب وحدات التشغيل الزمني.
