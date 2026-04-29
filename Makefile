PYTHON := python3

.PHONY: help check run_hospital run_authentication run_appointment run_prescription run_client run_phase1_example

help:
	@echo "Available targets:"
	@echo "  make check               - Syntax-check all Python files"
	@echo "  make run_hospital        - Start hospital_server.py"
	@echo "  make run_authentication  - Start authentication_server.py"
	@echo "  make run_appointment     - Start appointment_server.py"
	@echo "  make run_prescription    - Start prescription_server.py"
	@echo "  make run_client USER=<username> PASS=<password> - Start client.py"
	@echo "  make run_phase1_example  - Example Phase 1 client invocation"
	@echo ""
	@echo "Start order required by the project:"
	@echo "  1. make run_hospital"
	@echo "  2. make run_authentication"
	@echo "  3. make run_appointment"
	@echo "  4. make run_prescription"
	@echo "  5. make run_client USER=<username> PASS=<password>"
	@echo "  6. make run_client USER=<username> PASS=<password>"

check:
	$(PYTHON) -m py_compile common.py authentication_server.py appointment_server.py prescription_server.py hospital_server.py client.py

run_hospital:
	$(PYTHON) hospital_server.py

run_authentication:
	$(PYTHON) authentication_server.py

run_appointment:
	$(PYTHON) appointment_server.py

run_prescription:
	$(PYTHON) prescription_server.py

run_client:
	@if [ -z "$(USER)" ] || [ -z "$(PASS)" ]; then \
		echo "Usage: make run_client USER=<username> PASS=<password>"; \
		exit 1; \
	fi
	$(PYTHON) client.py "$(USER)" "$(PASS)"

run_phase1_example:
	$(PYTHON) client.py AvaMitchell 'qL4@zT81'
