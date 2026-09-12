"""Convert bliv-n4_vpl.txt (format: "GEN 1:1 text...") into per-chapter JSON files under api/pt-br/blivre/<book>/<chapter>.json"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_FILE = BASE_DIR / "bliv-n4_vpl.txt"
API_DIR = BASE_DIR.parent / "api" / "pt-br" / "blivre"

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
    with open(raw_path, encoding="utf-8") as f:
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


def write_chapter_json(book, book_name, chapter, verses, out_dir):
    data = {
        "book": book,
        "name": book_name,
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


def main():
    books = parse_raw(RAW_FILE)
    for book_code, chapters in books.items():
        book, book_name = BOOKS.get(book_code, (book_code.lower(), book_code))
        out_dir = API_DIR / book
        for chapter, verses in chapters.items():
            write_chapter_json(book, book_name, chapter, verses, out_dir)
    print(f"Done. Converted {len(books)} books.")


if __name__ == "__main__":
    main()
