# Changelog — Aodı-AgentX

## v1.0.0 — 2026-10-25
Initial release.

- **core (Python, صفر تبعيات):** stdlib HTTP API (server.py) + غلاف FastAPI اختياري (app_fastapi.py)؛ تنسيق مهام بالخيوط والمهام تسجل في ~/.aodix/tasks.jsonl
- **scanner:** 10 قواعد أمنية ساكنة متعددة اللغات (AX-S01..S10) بتنبيهاً عربياً عملياً
- **agents:** 4 أدوار (استطلاع/تدقيق/اختبارات/تكامل) بتعليمات صارمة JSON نظيف
- **orchestrator:** تدفق code_audit (static + وكلاء بالتوازي + دمج) وtest_gen ويأمر مخصصة
- **ollama_client:** كثيف عقد مع فشل سلس، فحص صحة متوازٍ، دفعات دائرية
- **netmgr (Go):** /health /sysinfo /ports (حتى 3000 منفذ، 200 goroutine) /probe
- **CLI (Node, صفر npm):** init · add-node · nodes · run · tasks · doctor
- **dashboard:** لوحة عربية RTL بصحة العقد وتشغيل المهام والتقارير
- **contracts:** AgentXProof.sol (تسجيل بصمات اختياري) + أداة anchor.js
- **tests:** 6 اختبارات بلا شبكة + CI (pytest-free unittest · go vet/build · node --check)
- **مثال حي:** examples/vuln_demo.py يعث السبع الثغرة في فحص واحد
