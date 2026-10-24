#!/usr/bin/env python3
# ملف تجريبي عمداً — لعرض قدرات Aodı-AgentX في الفحص الأمني. لا تستعمل هذا النمط إنتاجاً.
import hashlib
import os
import pickle
import subprocess

DATABASE_PASSWORD = "SuperSecret2026"          # AX-S01: سر مثبت
API_KEY = "sk-live-very-long-token-here"       # AX-S01


def admin_login(user_input):
    # AX-S02: تنفيذ ديناميكي من مدخل مستخدم
    return eval(user_input)


def run_backup(path):
    # AX-S03: شل مباشرة من مدخل
    os.system("tar -czf backup.tgz " + path)


def fetch_user(user_id):
    # AX-S05: بناء SQL بتنسيق
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)


def load_state(blob):
    # AX-S06: إزالة تسلسل غير آمنة
    return pickle.loads(blob)


def make_token(parts):
    # AX-S07: عشوائية أمنية لا صلاحية لها
    import random
    return random.choice(parts)
