"""Upload JSONL file and create a batch. Saves batch_id to a tracker file."""
import argparse, json, os, sys
from openai import OpenAI

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='JSONL file with batch requests')
    ap.add_argument('--tracker', required=True, help='Path to save batch metadata JSON')
    ap.add_argument('--description', default='K-curve eval batch')
    args = ap.parse_args()

    client = OpenAI()
    print(f"Uploading {args.input}...")
    with open(args.input, 'rb') as f:
        file_obj = client.files.create(file=f, purpose='batch')
    print(f"  uploaded: file_id={file_obj.id}")

    print("Creating batch...")
    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint='/v1/chat/completions',
        completion_window='24h',
        metadata={'description': args.description},
    )
    print(f"  batch_id={batch.id}  status={batch.status}")
    tracker = {
        'batch_id': batch.id,
        'input_file_id': file_obj.id,
        'description': args.description,
        'input_path': args.input,
        'status': batch.status,
        'created_at': batch.created_at,
    }
    with open(args.tracker, 'w') as f:
        json.dump(tracker, f, indent=2)
    print(f"Wrote tracker to {args.tracker}")

if __name__ == '__main__':
    main()
