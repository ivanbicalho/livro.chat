"""Convert bliv-n4_vpl.txt (format: "GEN 1:1 text...") into per-chapter JSON files under api/pt-br/blivre/<book>/<chapter>.json"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_FILE = BASE_DIR / "bliv-n4_vpl.txt"
PT_BR_DIR = BASE_DIR.parent / "public" / "api" / "pt-br"
API_DIR = PT_BR_DIR / "blivre"

LINE_PATTERN = re.compile(r"^(\S+)\s+(\d+):(\d+)\s+(.*)$")

BOOKS = {
    "GEN": ("genesis", "Gênesis"),
    "EXO": ("exodo", "Êxodo"),
    "LEV": ("levitico", "Levítico"),
    "NUM": ("numeros", "Números"),
    "DEU": ("deuteronomio", "Deuteronômio"),
    "JOS": ("josue", "Josué"),
    "JDG": ("juizes", "Juízes"),
    "RUT": ("rute", "Rute"),
    "1SA": ("1samuel", "1 Samuel"),
    "2SA": ("2samuel", "2 Samuel"),
    "1KI": ("1reis", "1 Reis"),
    "2KI": ("2reis", "2 Reis"),
    "1CH": ("1cronicas", "1 Crônicas"),
    "2CH": ("2cronicas", "2 Crônicas"),
    "EZR": ("esdras", "Esdras"),
    "NEH": ("neemias", "Neemias"),
    "EST": ("ester", "Ester"),
    "JOB": ("jo", "Jó"),
    "PSA": ("salmos", "Salmos"),
    "PRO": ("proverbios", "Provérbios"),
    "ECC": ("eclesiastes", "Eclesiastes"),
    "SOL": ("canticos", "Cânticos"),
    "ISA": ("isaias", "Isaías"),
    "JER": ("jeremias", "Jeremias"),
    "LAM": ("lamentacoes", "Lamentações"),
    "EZE": ("ezequiel", "Ezequiel"),
    "DAN": ("daniel", "Daniel"),
    "HOS": ("oseias", "Oséias"),
    "JOE": ("joel", "Joel"),
    "AMO": ("amos", "Amós"),
    "OBA": ("obadias", "Obadias"),
    "JON": ("jonas", "Jonas"),
    "MIC": ("miqueias", "Miquéias"),
    "NAH": ("naum", "Naum"),
    "HAB": ("habacuque", "Habacuque"),
    "ZEP": ("sofonias", "Sofonias"),
    "HAG": ("ageu", "Ageu"),
    "ZEC": ("zacarias", "Zacarias"),
    "MAL": ("malaquias", "Malaquias"),
    "MAT": ("mateus", "Mateus"),
    "MAR": ("marcos", "Marcos"),
    "LUK": ("lucas", "Lucas"),
    "JOH": ("joao", "João"),
    "ACT": ("atos", "Atos"),
    "ROM": ("romanos", "Romanos"),
    "1CO": ("1corintios", "1 Coríntios"),
    "2CO": ("2corintios", "2 Coríntios"),
    "GAL": ("galatas", "Gálatas"),
    "EPH": ("efesios", "Efésios"),
    "PHI": ("filipenses", "Filipenses"),
    "COL": ("colossenses", "Colossenses"),
    "1TH": ("1tessalonicenses", "1 Tessalonicenses"),
    "2TH": ("2tessalonicenses", "2 Tessalonicenses"),
    "1TI": ("1timoteo", "1 Timóteo"),
    "2TI": ("2timoteo", "2 Timóteo"),
    "TIT": ("tito", "Tito"),
    "PHM": ("filemom", "Filemom"),
    "HEB": ("hebreus", "Hebreus"),
    "JAM": ("tiago", "Tiago"),
    "1PE": ("1pedro", "1 Pedro"),
    "2PE": ("2pedro", "2 Pedro"),
    "1JO": ("1joao", "1 João"),
    "2JO": ("2joao", "2 João"),
    "3JO": ("3joao", "3 João"),
    "JUD": ("judas", "Judas"),
    "REV": ("apocalipse", "Apocalipse"),
}


def parse_raw(raw_path):
    """Return dict: book_code -> chapter_number -> verse_number -> text"""
    books = {}
    with open(raw_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = LINE_PATTERN.match(line)
            if not match:
                continue
            book_code, chapter, verse, text = match.groups()
            chapters = books.setdefault(book_code, {})
            verses = chapters.setdefault(int(chapter), {})
            verses[int(verse)] = text
    return books


def write_chapter_json(book, chapter, verses, out_dir):
    data = {
        "book": book,
        "chapter": chapter,
        "verses": [
            {
                "verse": verse_number,
                "segments": [{"speaker": "narrator", "text": verses[verse_number]}],
            }
            for verse_number in sorted(verses)
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{chapter}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def update_init_json(api_dir, pt_br_dir):
    """Rebuild the "books" list in init.json (chapters/verseCount) from the generated chapter files."""
    init_path = pt_br_dir / "init.json"
    with open(init_path, encoding="utf-8") as f:
        init_data = json.load(f)

    books = []
    for book_dir, book_name in BOOKS.values():
        chapter_dir = api_dir / book_dir
        if not chapter_dir.is_dir():
            continue
        chapter_files = sorted(chapter_dir.glob("*.json"), key=lambda p: int(p.stem))
        verse_count = []
        for chapter_file in chapter_files:
            with open(chapter_file, encoding="utf-8") as f:
                verse_count.append(len(json.load(f)["verses"]))
        books.append(
            {
                "book": book_dir,
                "name": book_name,
                "chapters": len(chapter_files),
                "verseCount": verse_count,
            }
        )

    init_data["books"] = books
    with open(init_path, "w", encoding="utf-8") as f:
        json.dump(init_data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def main():
    books = parse_raw(RAW_FILE)
    for book_code, chapters in books.items():
        book, _ = BOOKS.get(book_code, (book_code.lower(), book_code))
        out_dir = API_DIR / book
        for chapter, verses in chapters.items():
            write_chapter_json(book, chapter, verses, out_dir)
    update_init_json(API_DIR, PT_BR_DIR)
    print(f"Done. Converted {len(books)} books.")


if __name__ == "__main__":
    main()
