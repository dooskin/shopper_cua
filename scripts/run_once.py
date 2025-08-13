import os
import json
import uuid
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
VENDOR_CLI = ROOT / "vendor" / "openai-cua-sample-app" / "cli.py"


def fail(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def require_env(keys: list[str]) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        fail(f"Missing env vars: {', '.join(missing)}")


def build_start_url(
    base_domain: str, start_path: str, persona_id: str, variant: str, run_id: str
) -> str:
    if not start_path.startswith("/"):
        start_path = "/" + start_path
    return (
        f"https://{base_domain}{start_path}?uxagent=1&persona={persona_id}"
        f"&variant={variant}&run={run_id}"
    )


def build_prompt(persona: dict, start_url: str) -> str:
    goals = "; ".join(persona.get("goals", []))
    style = persona.get("style", "neutral")
    profile = persona.get("profile", {})
    return (
        f"You are a shopper persona: {persona['name']} ({persona['id']}). "
        f"Style: {style}. Profile: {json.dumps(profile)}. "
        f"Start at {start_url} and accomplish: {goals}. "
        "If a cookie/consent banner appears, accept it. Use site nav or search. "
        "Once a product is added to cart, stop."
    )


def main() -> None:
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--persona", required=True, help="path to persona JSON (under personas/)"
    )
    parser.add_argument("--variant", required=True, choices=["A", "B"])
    parser.add_argument(
        "--show", action="store_true", help="if supported by vendor CLI, show UI"
    )
    args = parser.parse_args()

    require_env(
        [
            "OPENAI_API_KEY",
            "BROWSERBASE_API_KEY",
            "BROWSERBASE_PROJECT_ID",
            "SHOP_BASE_DOMAIN",
        ]
    )
    start_path = os.environ.get("SHOP_START_PATH", "/")
    base_domain = os.environ["SHOP_BASE_DOMAIN"]

    persona_path = Path(args.persona)
    persona = json.loads(persona_path.read_text())
    run_id = str(uuid.uuid4())[:8]
    start_url = build_start_url(
        base_domain, start_path, persona["id"], args.variant, run_id
    )
    prompt = build_prompt(persona, start_url)

    if not VENDOR_CLI.exists():
        fail(
            f"Vendor CLI not found at {VENDOR_CLI}. Did you init the submodule?"
        )

    cmd = [
        sys.executable,
        str(VENDOR_CLI),
        "--computer",
        "browserbase",
        "--start-url",
        start_url,
        "--input",
        prompt,
    ]
    if args.show:
        cmd.append("--show")

    print(
        f"[run {run_id}] persona={persona['id']} variant={args.variant} url={start_url}"
    )
    code = subprocess.call(cmd, env=os.environ.copy())
    if code != 0:
        fail(f"Vendor CLI exited with {code}")


if __name__ == "__main__":
    main()
