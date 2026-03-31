#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line wrapper for OpenRouter chat completions.
"""

import argparse
import json
import sys

from openrouter_client import DEFAULT_OPENROUTER_MODEL, request_openrouter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Call OpenRouter chat completions from the command line."
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--prompt", help="User prompt")
    input_group.add_argument("--prompt-file", help="Read prompt from file")
    input_group.add_argument("--messages", help="JSON file with messages list")

    parser.add_argument("--system", help="System prompt")
    parser.add_argument("--model", default=DEFAULT_OPENROUTER_MODEL)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--extra", help="JSON file with extra payload")
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--output", help="Save full JSON response to file")
    return parser.parse_args()


def read_text_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read().strip()


def load_json_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_messages(args):
    if args.messages:
        payload = load_json_file(args.messages)
        if isinstance(payload, dict) and "messages" in payload:
            return payload["messages"]
        return payload

    prompt = None
    if args.prompt_file:
        prompt = read_text_file(args.prompt_file)
    elif args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if not prompt:
        raise ValueError("Missing prompt. Use --prompt, --prompt-file, or --messages.")

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": prompt})
    return messages


def main():
    args = parse_args()
    messages = build_messages(args)
    extra_payload = load_json_file(args.extra) if args.extra else None

    content, raw = request_openrouter(
        args.model,
        messages,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        extra_payload=extra_payload,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            json.dump(raw, file, ensure_ascii=False, indent=2)

    if args.print_json:
        print(json.dumps(raw, ensure_ascii=False, indent=2))
    else:
        print(content)


if __name__ == "__main__":
    main()
