"""Aodı-AgentX — static security scanner (multi-language regex audit layer)."""
import re
from dataclasses import dataclass, asdict

import config


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str   # high / med / low
    evidence: str
    message: str


# (id, severity, regex, message) — معاير تفتيش ثابتة لا ادعاء ذكاء
RULES = [
    ("AX-S01", "high",
     re.compile(r"(?i)\b(password|passwd|api[_-]?key|secret|access[_-]?token|private[_-]?key)\b\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
     "قيمة سرية مثبتة في الكود — انقلها إلى متغيرات بيئة أو مخزن أسرار."),
    ("AX-S02", "high",
     re.compile(r"(?i)\b(eval|exec)\s*\(|new\s+Function\s*\("),
     "تنفيذ ديناميكي للكود (eval / exec) — أعد الهيكلة؛ مدخل طرف ثالث في هذا المسار ثغرة."),
    ("AX-S03", "high",
     re.compile(r"\b(shell\s*=\s*True|os\.system\s*\(|child_process|Runtime\s*\.\s*getRuntime)"),
     "استخدام شَل قد يسمح بحقن الأوامر — تحقق من مصدر كل سلسلة تمر إليه."),
    ("AX-S04", "med",
     re.compile(r"(?i)\b(md5|sha1)\s*\("),
     "دالة هاش ضعيفة معروفة الاصطدام — استعمل sha256 أو bcrypt."),
    ("AX-S05", "high",
     re.compile(r"(?i)(\b(?:execute|cursor|query)\s*\(\s*[fr]?['\"][^'\"]*(?:%s|\{|\$\{))|((?:[fr]?['\"]) ?\s*(?:select|insert|update|delete)\s[^'\"]*(?:%s|\{|\$\{))"),
     "بناء استعلام SQL بتنسيق سلسلة — استبدل بالمعاملات البارامترية."),
    ("AX-S06", "high",
     re.compile(r"(?i)\b(pickle\.loads?\s*\(|yaml\.load\s*\()"),
     "إزالة تسلسل غير آمنة لبيانات غير موثوقة — استعمل yaml.safe_load وتجنب pickle."),
    ("AX-S07", "med",
     re.compile(r"(?i)\b(random\.(choice|randint|random))\b.*\b(token|otp|secret|password|session)\b"),
     "عشوائية غير صلاحية للاستخدام الأمني — استعمل مكتبة secrets أو os.urandom."),
    ("AX-S08", "low",
     re.compile(r"(?i)(debug\s*=\s*True|host\s*=\s*['\"]0\.0\.0\.0['\"]|NODE_ENV[^\n]*development)"),
     "أوضاع تطوير مكشوفة قد تسرب التتبع والإعدادات في بيئة التشغيل."),
    ("AX-S09", "med",
     re.compile(r"(?i)(chmod\s+777|Access[-_]Control[-_]Allow[-_]Origin['\"]?\]\]?\s*[:,=]\s*['\"]\*['\"]|origin\s*:\s*['\"]\*['\"])"),
     "صلاحيات أو CORS واسعة جداً — حدّدها لعميل أو نطاق معلوم."),
    ("AX-S10", "med",
     re.compile(r"(?i)(innerHTML\s*=|dangerouslySetInnerHTML|document\.write\s*\()"),
     "حقن DOM مباشر ببيانات غير موثوقة — استعمل textContent أو ترميز HTML المشفر."),
]

RULES_BY_ID = {r[0]: r for r in RULES}


def scan_file(path, rel):
    """سجل Findings لملف واحد (يتجاهل الملفات الكبيرة)."""
    try:
        data = open(path, "r", encoding="utf-8", errors="ignore").read(
        )[: config.MAX_FILE_BYTES]
    except OSError:
        return []
    out = []
    for i, line in enumerate(data.splitlines(), start=1):
        for rule_id, sev, rx, msg in RULES:
            if rx.search(line):
                out.append(Finding(rel, i, rule_id, sev, line.strip()[:160], msg))
    return out


def to_dict(f):
    return asdict(f)
