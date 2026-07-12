# Production-style serving — vLLM on AMD GPU (ROCm), Phase 5

Goal (Epic F2): run the identical stack against vLLM on the AMD developer GPU cloud so we can
validate production-style serving (throughput, concurrency) before any managed-cloud migration.
Same OpenAI-compatible API surface as Ollama, so adapters only change `base_url`.

## 1. Environment (ROCm)

```bash
# AMD ROCm box (MI-series GPU). Verify the GPU is visible:
rocminfo | grep -i "Marketing Name"
rocm-smi

# vLLM with ROCm backend (build or use the AMD-maintained image):
docker run -it --rm \
  --device=/dev/kfd --device=/dev/dri --group-add video \
  --shm-size 16g -p 8000:8000 \
  rocm/vllm:latest \
  vllm serve Qwen/Qwen2.5-14B-Instruct \
    --port 8000 --max-model-len 8192 --dtype float16
```

Serve the lighter model on a second port (or a second GPU) to mirror the per-role split:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8001 --dtype float16
```

## 2. Point the agents at vLLM

```python
_FAST  = ModelConfig(provider="vllm", model="meta-llama/Llama-3.1-8B-Instruct",
                     base_url="http://<amd-box>:8001/v1", temperature=0.0)
_SMART = ModelConfig(provider="vllm", model="Qwen/Qwen2.5-14B-Instruct",
                     base_url="http://<amd-box>:8000/v1", temperature=0.1)
```

The REST tool layer + MCP servers run as local processes on the same box (EngDesign §12) so
tool-call latency stays comparable to the Ollama phase:

```bash
uvicorn services.app:app --host 0.0.0.0 --port 8080 &
python -m mcp_servers.seed_kb
```

## 3. What to measure (document for the blog, Epic G)

- Throughput: orders/sec sustained before agent decisions lag the engine event stream.
- Concurrency: p50/p95 tool-call + model latency under the `rush` scenario vs Ollama.
- Determinism: pin `--seed` and temperature; note any nondeterminism vs the Ollama run.
- Delta table: Ollama(dev) vs vLLM(prod-style) for each of the 3 load profiles.

## 4. Open items (EngDesign §14)

- Exact open-source model(s) validated on the AMD box — record final choice here once pinned.
- Vector store choice (Chroma vs FAISS) for the Knowledge MCP server — pick what runs cleanest
  alongside vLLM on ROCm; the v1 `KnowledgeStore` is a drop-in to replace.
