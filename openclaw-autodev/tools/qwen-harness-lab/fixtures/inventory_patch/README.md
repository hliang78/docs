Qwen harness lab fixture: `inventory_patch`

Goal:
- Fix one small regression in `inventory.py`.
- Keep the patch limited to `inventory.py`.
- Run `python3 -m unittest -q` before claiming success.

Rules:
- Do not add dependencies.
- Do not edit tests unless the task explicitly says the tests are wrong.
- Final response should use the OpenClaw footer contract.
