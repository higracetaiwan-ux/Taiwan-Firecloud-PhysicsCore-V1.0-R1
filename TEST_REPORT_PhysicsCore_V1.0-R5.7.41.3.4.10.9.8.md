# Test Report — PhysicsCore V1.0-R5.7.41.3.4.10.9.8

## Targeted

- 新 `.10.9.8` DWD tests：4/4 PASS
- 既有 DWD runtime/provider compatibility tests：PASS

## Full working-tree regression

- **726/726 PASS**
- 1 個既有 pandas FutureWarning（非 failure）

## 新測項

1. shared cache root 不受 release working directory 影響；
2. explicit state-dir contract 保持相容；
3. thread-local Session：同 thread reuse、不同 thread 不共享；
4. FIELD_FETCH audit 保留 shared-cache / connection-reuse provenance；
5. 舊 `requests.get` monkeypatch compatibility 保留。

## Fresh-extract

- FULL-CLEAN fresh-extract：**726/726 PASS**
- 1 個既有 pandas FutureWarning
- Release ZIP：852 entries
- `__pycache__` / `.pytest_cache` / `.pyc` / `.pyo`：0
