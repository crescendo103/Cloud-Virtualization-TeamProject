FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/2. Scheduler:/app/3. Trainer"

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY ["1. Input", "/app/1. Input"]
COPY ["2. Scheduler", "/app/2. Scheduler"]
COPY ["3. Trainer", "/app/3. Trainer"]
COPY ["4. Dashboard", "/app/4. Dashboard"]

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
