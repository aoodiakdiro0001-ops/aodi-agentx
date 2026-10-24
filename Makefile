.PHONY: ci-server ci-cli build-netmgr tests dev demo

# Server core (stdlib) — يعمل في كل مكان
ci-server: ## запуск core API على 8787
	python3 core/server.py --port 8787

# فحوصات كاملة (بلا شبكة)
tests:
	python3 tests/test_scanner.py -v
	node --check cli/index.js
	cd netmgr && gofmt -w . && go vet ./... && go build ./.

# بناء netmgr darwin مسلح
build-netmgr:
	cd netmgr && go build -o ../bin/agentx-netmgr-darwin .

# ديمو فوري: تدقيق مجلد examples عبر كل العقد الصحية
demo:
	python3 -c "import sys; sys.path.insert(0,'core'); \
import orchestrator, json; \
r = orchestrator.new_task('code_audit', {'path':'examples'}); print('task:', r['id'])"
	@echo "تتبع النتيجة: GET /api/tasks/<id>"
