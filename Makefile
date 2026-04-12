.PHONY: dev-backend dev-frontend install-backend install-frontend

dev-backend:
	cd backend && ./.venv/bin/uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

install-backend:
	cd backend && python3 -m venv .venv && ./.venv/bin/pip install -U pip && ./.venv/bin/pip install -r requirements.txt

install-frontend:
	cd frontend && npm install
