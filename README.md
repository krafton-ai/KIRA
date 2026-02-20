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


For more details, visit our [blog post](https://krafton-ai.github.io/blog/terminus_kira_en/).           

---

## Citing Us

If you found Terminus-KIRA useful, please cite us as:

```bibtex
@misc{terminuskira2026,
      title={Terminus-KIRA: Terminus-KIRA: Boosting Frontier Model Performance on Terminal-Bench with Minimal Harness },
      author={Minseok Choi and Wooseong Chung and Yun Jegal and Jiho Jeon and Giyoung Jung and Seungjin Kwon and Gisang Lee and Hyogon Ryu and Myungseok Oh and Hara Kang and Kangwook Lee},
      year={2026},
      url={https://github.com/krafton-ai/kira},
}
```

---
KRAFTON AI & Ludo Robotics
