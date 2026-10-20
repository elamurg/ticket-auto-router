
FROM python:3.12-slim AS builder
WORKDIR /app

COPY pyproject.toml README.md ./
COPY ./src ./src

# Install the CPU-only torch wheel first. Left to its own defaults, pip
# resolves torch (pulled in transitively by sentence-transformers) from
# PyPI's default index, which on Linux means the CUDA-enabled build, several
# GB of NVIDIA driver libraries this container has no GPU to use. Satisfying
# the dependency with the CPU wheel up front means the later `pip install .`
# finds torch already installed and doesn't re-fetch the CUDA build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir .

FROM python:3.12-slim AS runtime
WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app/src ./src

RUN useradd -m appuser
USER appuser

CMD ["uvicorn", "router.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
