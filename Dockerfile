FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

WORKDIR /workspace

RUN apt-get update && apt-get install -y git

RUN git clone https://github.com/ACE-Step/ACE-Step-1.5.git /workspace/ACE-Step-1.5

WORKDIR /workspace/ACE-Step-1.5

RUN pip install --no-cache-dir --ignore-installed -e acestep/third_parts/nano-vllm
RUN pip install --no-cache-dir torch==2.10.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu128
RUN pip install --no-cache-dir -e .

EXPOSE 8001

CMD ["python3", "acestep/api_server.py", "--port", "8001", "--server-name", "0.0.0.0"]
