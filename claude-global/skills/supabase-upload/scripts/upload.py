#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Upload CLI Tool.

Usage:
    python upload.py <file_path> [--folder <folder>] [--url-only]
    python upload.py list [--folder <folder>]
    python upload.py delete <storage_path>
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from supabase_client import upload_file, upload_base64, delete_file, list_files


def main():
    parser = argparse.ArgumentParser(
        description="Supabase Storage Upload Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload.py image.png
  python upload.py image.png --folder images
  python upload.py image.png --url-only
  python upload.py list --folder images
  python upload.py delete images/image.png
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Upload command (default)
    upload_parser = subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("file", help="Local file path to upload")
    upload_parser.add_argument("--folder", "-f", default="", help="Folder path in bucket")
    upload_parser.add_argument("--name", "-n", help="Custom filename")
    upload_parser.add_argument("--url-only", action="store_true", help="Only print the URL")

    # List command
    list_parser = subparsers.add_parser("list", help="List files in a folder")
    list_parser.add_argument("--folder", "-f", default="", help="Folder path in bucket")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a file")
    delete_parser.add_argument("path", help="Storage path of the file to delete")

    args = parser.parse_args()

    # If no subcommand, treat first positional arg as file to upload
    if not args.command:
        # Check if there's a positional argument that looks like a file
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # Re-parse with upload as default command
            sys.argv.insert(1, "upload")
            args = parser.parse_args()
        else:
            parser.print_help()
            return 1

    try:
        if args.command == "upload":
            url = upload_file(args.file, folder=args.folder, filename=args.name)

            if args.url_only:
                print(url)
            else:
                print(f"Upload successful!")
                print(f"  URL: {url}")
                print(f"  File: {Path(args.file).name}")

        elif args.command == "list":
            files = list_files(args.folder)
            if not files:
                print("No files found")
            else:
                print(f"Files in '{args.folder or '/'}':")
                for f in files:
                    name = f.get("name", "unknown")
                    size = f.get("metadata", {}).get("size", "?")
                    print(f"  {name} ({size} bytes)")

        elif args.command == "delete":
            delete_file(args.path)
            print(f"Deleted: {args.path}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
