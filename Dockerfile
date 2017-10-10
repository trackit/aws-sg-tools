FROM python:2.7

RUN mkdir /app

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python" ]