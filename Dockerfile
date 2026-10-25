FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REELS_HOST=0.0.0.0 \
    REELS_PORT=8080 \
    REELS_DATABASE=/app/data/library.sqlite3 \
    REELS_SESSION_FILE=/app/sessions/instagram.cookies

WORKDIR /app
COPY requirements.txt requirements-sync.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-sync.txt \
    && groupadd --gid 10001 reels \
    && useradd --uid 10001 --gid reels --no-create-home reels \
    && mkdir -p /app/data /app/sessions /app/config \
    && chown -R reels:reels /app \
    && chmod 700 /app/sessions /app/config
COPY --chown=reels:reels reels_library ./reels_library
COPY --chown=reels:reels LICENSE THIRD_PARTY_NOTICES.md ./

USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3).read()"
CMD ["python", "-m", "reels_library"]
