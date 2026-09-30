FROM python:3.11-slim

RUN useradd -m -u 1000 user

WORKDIR /app
RUN chown user:user /app

USER user
ENV PATH="/home/user/.local/bin:$PATH"

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

EXPOSE 7860

CMD chainlit run morpheus_ai.py --host 0.0.0.0 --port $PORT