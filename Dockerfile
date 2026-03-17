FROM python:3.11

WORKDIR /app

COPY . .

# install python deps
RUN pip install -r backend/requirements.txt

# install node + build frontend
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app/frontend
RUN npm install && npm run build

# back to app root
WORKDIR /app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
