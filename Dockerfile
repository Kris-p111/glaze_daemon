FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY --chmod=755 *.py .

RUN pip install mysql-connector-python fastapi[standard] pillow
EXPOSE 8000

CMD ["fastapi", "run", "backend.py"]
