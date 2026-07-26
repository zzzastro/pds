import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / 'data' / 'raw' / 'pds_dataset.txt'
OUTPUT_DIR = BASE_DIR / 'apps' / 'plagiarism' / 'static' / 'dataset'
CHUNK_SIZE = 500
FILES_PER_DIR = 100

def main():
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]

    total_lines = len(lines)
    total_chunks = (total_lines + CHUNK_SIZE - 1) // CHUNK_SIZE

    for i in range(0, total_lines, CHUNK_SIZE):
        chunk = lines[i:i + CHUNK_SIZE]
        chunk_num = i // CHUNK_SIZE
        subdir = OUTPUT_DIR / 'chunks' / str(chunk_num // FILES_PER_DIR)
        subdir.mkdir(parents=True, exist_ok=True)
        fname = f'{chunk_num:03d}.json'
        with open(subdir / fname, 'w', encoding='utf-8') as out:
            json.dump(chunk, out, ensure_ascii=False)

    index = {
        'total_lines': total_lines,
        'chunk_size': CHUNK_SIZE,
        'total_chunks': total_chunks,
        'files_per_dir': FILES_PER_DIR,
    }
    with open(OUTPUT_DIR / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)

    sample = lines[:200]
    with open(OUTPUT_DIR / 'sample.json', 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False)

    print(f'Done: {total_lines} lines, {total_chunks} chunks, {total_chunks // FILES_PER_DIR + (1 if total_chunks % FILES_PER_DIR else 0)} subdirs')

if __name__ == '__main__':
    main()
