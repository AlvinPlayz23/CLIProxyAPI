#!/usr/bin/env python3
"""Generate an OpenCode V2 provider config from CLIProxyAPI's unified /v1/models."""

import argparse
import json
import os
import sys
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("CLIPROXYAPI_BASE_URL", "http://127.0.0.1:8317/v1"))
    parser.add_argument("--api-key", default=os.environ.get("CLIPROXYAPI_API_KEY", ""))
    parser.add_argument("--output", default="opencode.json")
    parser.add_argument("--provider", default="cliproxy")
    parser.add_argument("--name", default="CLIProxyAPI")
    parser.add_argument("--default", default="")
    args = parser.parse_args()

    url = args.base_url.rstrip("/") + "/models"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    if args.api_key:
        request.add_header("Authorization", "Bearer " + args.api_key)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except Exception as exc:
        print(f"failed to fetch {url}: {exc}", file=sys.stderr)
        return 1

    models = payload.get("data", [])
    if not isinstance(models, list) or not models:
        print("CLIProxyAPI returned no models", file=sys.stderr)
        return 1

    model_map = {}
    for item in models:
        if not isinstance(item, dict):
            continue
        model_id = str(item.get("id", "")).strip()
        if not model_id:
            continue
        model_map[model_id] = {"name": str(item.get("name") or model_id)}

    if not model_map:
        print("CLIProxyAPI returned no usable model IDs", file=sys.stderr)
        return 1

    config = {
        "$schema": "https://opencode.ai/config.json",
        "providers": {
            args.provider: {
                "name": args.name,
                "package": "@opencode/ai/providers/openai-compatible",
                "settings": {
                    "baseURL": args.base_url.rstrip("/"),
                },
                "models": model_map,
            }
        },
    }
    if args.api_key:
        config["providers"][args.provider]["settings"]["apiKey"] = args.api_key
    if args.default:
        if args.default not in model_map:
            print(f"default model {args.default!r} is not present in /v1/models", file=sys.stderr)
            return 1
        config["model"] = f"{args.provider}/{args.default}"

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")

    print(f"wrote {len(model_map)} models to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
