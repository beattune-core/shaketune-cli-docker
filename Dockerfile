# --- Builder: compiles numpy/openblas, installs all Python deps ---
FROM python:3.12-alpine3.22 AS builder

RUN apk add --no-cache \
  git \
  openblas-dev \
  gcc \
  g++ \
  musl-dev \
  gfortran

RUN pip install --no-cache-dir uv

RUN git clone --depth=1 https://github.com/Klipper3d/klipper.git /app/klipper
RUN git clone --depth=1 https://github.com/Frix-x/klippain-shaketune.git /app/klippain-shaketune

RUN uv venv /app/.venv
RUN uv pip install --python /app/.venv/bin/python \
  -r /app/klippain-shaketune/requirements.txt
RUN uv pip install --python /app/.venv/bin/python gradio

# --- Runtime: only what is needed to run the app ---
FROM python:3.12-alpine3.22

# git: required at runtime by GitPython (shaketune dependency)
# openblas: shared library required by numpy at runtime
RUN apk add --no-cache git openblas

COPY --from=builder /app/klipper /app/klipper
COPY --from=builder /app/klippain-shaketune /app/klippain-shaketune
COPY --from=builder /app/.venv /app/.venv
COPY app/main.py /app/main.py

ENV PYTHONPATH=/app/klippain-shaketune
ENV MPLBACKEND=Agg

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:7860 || exit 1

EXPOSE 7860

CMD ["/app/.venv/bin/python", "/app/main.py"]
