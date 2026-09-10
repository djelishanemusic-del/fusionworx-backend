# Install httpx for the wrapper
RUN pip install --no-cache-dir httpx

# Copy the wrapper into the image
COPY runpod_wrapper.py /workspace/runpod_wrapper.py

EXPOSE 8001

CMD ["python3", "/workspace/runpod_wrapper.py"]
