<p align="center">
  <h1 align="center">Terminus-KIRA</h1>
  <p align="center">
    A smarter agent harness for <a href="https://github.com/TerminalBench/TerminalBench">TerminalBench</a>, built on top of <a href="https://github.com/TerminalBench/TerminalBench">Terminus 2</a>
    <br/>
    <em>Simple fixes, significant gains.</em>
  </p>
</p>

---

## Usage

```bash
uv run harbor run \
    --dataset terminal-bench-sample@2.0 \
    --n-tasks 1 \
    --agent-import-path "terminus_kira.terminus_kira:TerminusKIRA" \
    --model anthropic/claude-opus-4-6 \
    --env docker \
    -n 1
```
  


---
KRAFTON AI & Ludo Robotics
