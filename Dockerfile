FROM python:3.10-slim

WORKDIR /usr/src/app

COPY --chmod=755 *.py .

RUN pip install --default-timeout=120 --retries=5 --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --default-timeout=120 --retries=5 --no-cache-dir mysql-connector-python fastapi[standard] transformers chromadb Pillow

#RUN pip install mysql-connector-python fastapi[standard] torch transformers chromadb Pillow
EXPOSE 8000

CMD ["fastapi", "run", "backend.py"]
