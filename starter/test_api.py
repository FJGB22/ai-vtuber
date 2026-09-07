"""
Isolates the LLM call so errors are readable.

    python test_api.py

Tests three things in order: that your .env loaded, that a plain request works,
and that streaming works. It stops at the first failure and tells you what broke.
"""
import sys
import traceback

from openai import OpenAI

from config import cfg


def main() -> None:
    print("=" * 60)
    print("1. Config")
    print("=" * 60)
    print(f"  base_url : {cfg.llm_base_url}")
    print(f"  model    : {cfg.llm_model}")
    key = cfg.llm_api_key
    if not key or key in ("not-needed", "your-key-here"):
        print("  api_key  : MISSING")
        print("\n  -> .env wasn't loaded, or you didn't replace 'your-key-here'.")
        print("     Check the file is named exactly .env (not .env.txt) and lives")
        print("     in this folder next to test_api.py.")
        sys.exit(1)
    print(f"  api_key  : {key[:6]}...{key[-4:]}  (length {len(key)})")

    client = OpenAI(base_url=cfg.llm_base_url, api_key=key)

    print("\n" + "=" * 60)
    print("2. Plain request")
    print("=" * 60)
    try:
        r = client.chat.completions.create(
            model=cfg.llm_model,
            messages=[{"role": "user", "content": "Say the word 'working' and nothing else."}],
            max_tokens=20,
        )
        print(f"  reply: {r.choices[0].message.content!r}")
    except Exception:
        print("  FAILED:\n")
        traceback.print_exc()
        print("\n  Common causes:")
        print("   - wrong LLM_MODEL name (the error usually lists valid ones)")
        print("   - bad or not-yet-active API key")
        print("   - wrong LLM_BASE_URL")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("3. Streaming request")
    print("=" * 60)
    try:
        stream = client.chat.completions.create(
            model=cfg.llm_model,
            messages=[{"role": "user", "content": "Count from one to five, in words."}],
            max_tokens=40,
            stream=True,
        )
        chunks = 0
        print("  ", end="")
        for chunk in stream:
            piece = chunk.choices[0].delta.content or ""
            if piece:
                chunks += 1
                print(piece, end="", flush=True)
        print(f"\n  received {chunks} chunks")
        if chunks == 0:
            print("\n  -> Streaming returned nothing. This is why main.py hangs.")
            sys.exit(1)
    except Exception:
        print("  FAILED:\n")
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL GOOD - main.py should work.")
    print("=" * 60)


if __name__ == "__main__":
    main()
