import os
import sys
import time
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN_ONCE = ROOT / "scripts" / "run_once.py"
CONFIG = ROOT / "configs" / "batch.yaml"


def fail(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if not CONFIG.exists():
        fail(f"Missing config: {CONFIG}")
    if not RUN_ONCE.exists():
        fail(f"Missing script: {RUN_ONCE}")

    cfg = yaml.safe_load(CONFIG.read_text()) or {}
    start_url_path = cfg.get("start_url_path", "/")
    variants = cfg.get("variants", ["A", "B"]) or []
    personas = cfg.get("personas", []) or []
    runs_per = int(cfg.get("runs_per_persona_per_variant", 1))
    delay = int(cfg.get("delay_seconds_between_starts", 5))
    show = bool(cfg.get("debug_show_screens", False))

    # Export start path so run_once picks it up.
    os.environ["SHOP_START_PATH"] = str(start_url_path)

    for persona in personas:
        persona_path = ROOT / "personas" / persona
        if not persona_path.exists():
            fail(f"Persona not found: {persona_path}")
        for variant in variants:
            for i in range(runs_per):
                cmd = [
                    sys.executable,
                    str(RUN_ONCE),
                    "--persona",
                    str(persona_path),
                    "--variant",
                    str(variant),
                ]
                if show:
                    cmd.append("--show")
                print(
                    f"[batch] start persona={persona} variant={variant} iter={i+1}/{runs_per}"
                )
                code = subprocess.call(cmd, env=os.environ.copy())
                if code != 0:
                    fail(
                        f"Child run failed persona={persona} variant={variant} code={code}"
                    )
                if delay > 0:
                    time.sleep(delay)


if __name__ == "__main__":
    main()
