# Plan: splitting speaker segments in public/api/pt-br/blivre/**/*.json

Goal: every chapter file under `public/api/pt-br/blivre/<book>/<chapter>.json`
should match the target shape below — direct speech pulled out of the
`narrator` segment into its own segment, tagged with an english lowercase
`speaker` id (e.g. `god`, `adam`, `eve`, `moses`).

## Target shape

```json
{
    "book": "genesis",
    "name": "Gênesis",
    "chapter": 1,
    "verses": [
        {
            "verse": 1,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "No princípio criou Deus os céus e a terra."
                }
            ]
        },
        {
            "verse": 2,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E a terra estava desordenada e vazia, e as trevas estavam sobre a face do abismo, e o Espírito de Deus se movia sobre a face das águas."
                }
            ]
        },
        {
            "verse": 3,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E disse Deus:"
                },
                {
                    "speaker": "god",
                    "text": "Haja luz;"
                },
                {
                    "speaker": "narrator",
                    "text": "e houve luz."
                }
            ]
        },
        {
            "verse": 4,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E viu Deus que a luz era boa: e separou Deus a luz das trevas."
                }
            ]
        },
        {
            "verse": 5,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E chamou Deus à luz Dia, e às trevas chamou Noite: e foi a tarde e a manhã o primeiro dia."
                }
            ]
        },
        {
            "verse": 6,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E disse Deus:"
                },
                {
                    "speaker": "god",
                    "text": "Haja expansão em meio das águas, e separe as águas das águas."
                }
            ]
        },
        {
            "verse": 7,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E fez Deus a expansão, e separou as águas que estavam debaixo da expansão, das águas que estavam sobre a expansão: e foi assim."
                }
            ]
        },
        {
            "verse": 8,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E chamou Deus à expansão Céus: e foi a tarde e a manhã, o dia segundo."
                }
            ]
        },
        {
            "verse": 9,
            "segments": [
                {
                    "speaker": "narrator",
                    "text": "E disse Deus:"
                },
                {
                    "speaker": "god",
                    "text": "Juntem-se as águas que estão debaixo dos céus em um lugar, e descubra-se a porção seca;"
                },
                {
                    "speaker": "narrator",
                    "text": "e foi assim."
                }
            ]
        }
    ]
}
```

## Tool

Use `scripts/split_segments.py`, not manual JSON edits, for every change:

```
python3 scripts/split_segments.py <patch.json> [--dry-run]
```

Patch shape:

```json
{
  "operations": [
    {
      "file": "public/api/pt-br/blivre/genesis/1.json",
      "book": "genesis",
      "chapter": 1,
      "verse": 3,
      "segments": [
        { "speaker": "narrator", "text": "E disse Deus:" },
        { "speaker": "god", "text": "Haja luz;" },
        { "speaker": "narrator", "text": "e houve luz." }
      ]
    },
    {
      "file": "public/api/pt-br/blivre/genesis/2.json",
      "verse": 23,
      "action": "setSpeaker",
      "segmentIndex": 1,
      "speaker": "adam"
    }
  ]
}
```

- `book`/`chapter` on an operation are optional sanity checks against the
  file's own fields.
- Default action is `split` when `segments` is present, otherwise
  `setSpeaker`.
- `split` replaces a verse's whole `segments` array. The script rejects the
  write unless the joined text of the new segments matches the joined text of
  the old segments (ignoring quote characters/whitespace) — pass
  `"force": true` on the operation for an intentional text change (e.g.
  dropping a redundant `"(disse ela)"` attribution aside), which prints the
  diff as a warning instead of failing.
- `setSpeaker` only relabels one segment's `speaker` (`segmentIndex`, or
  omit it if the verse has exactly one segment) without touching text.
- One patch file can batch operations across many verses/files; the script
  loads each file once, applies all ops, then writes once.

## Per-chapter workflow

1. Read the chapter file (or a batch of chapters) to find verses containing
   reported speech (`disse`, `respondeu`, `clamou`, `falou`, quotation marks,
   etc.).
2. Decide the split for each such verse (see conventions below) — usually a
   narrator lead-in segment (`"E disse Deus:"`) plus one or more speaker
   segments, and a trailing narrator segment if the sentence resumes
   narration.
3. Write a scratch patch JSON (e.g. under `/tmp/`) with one `split`/
   `setSpeaker` operation per changed verse for that chapter (or batch of
   chapters/book).
4. Run the script with `--dry-run` first if the change set is large or
   uncertain, then run for real.
5. Validate the resulting file(s): `python3 -m json.tool <file>`.
6. Spot-check a diff (`git diff -- <file>`) before moving to the next
   chapter/book.
7. Present a batch (e.g. one chapter, or a handful of short chapters) to the
   user for review before continuing, per their preference for incremental
   review.

## Speaker naming conventions

- Always english, lowercase, no spaces (use `_` if a multi-word id is truly
  needed, but prefer a single word).
- `narrator` for all non-quoted narration.
- `god` for "Deus" / "SENHOR" / "SENHOR Deus" speaking.
- Named humans use their common english name: `adam`, `eve`, `cain`, `abel`,
  `lamech`, `noah`, `abraham`, `sarah`, `moses`, `pharaoh`, etc. Introduce a
  new id the first time that person speaks and reuse it consistently across
  chapters/books.
- Unnamed speakers get a descriptive id in english, e.g. `serpent`,
  `angel`, `servant`, `messenger`. If the same unnamed role recurs and is
  distinguishable (e.g. "an angel of the LORD" vs a generic messenger), keep
  ids consistent within a book; don't over-differentiate.
- A person referred to before they're formally named (e.g. "a mulher" before
  she's called "Eva") still gets their eventual name as the speaker id for
  consistency (`eve`), not a generic placeholder like `woman`.
- Crowds/groups speaking in unison can share one id relevant to the group,
  e.g. `people`, `disciples`, `pharisees` — do not invent one id per member
  unless individuals are distinguished in the text.
- Keep a running list of ids actually used in
  `/memories/repo/blivre-speaker-split.md` (session/repo memory) so ids stay
  consistent across books; update it as new speakers are introduced.

## Segment-splitting conventions

- Keep the narrator's lead-in phrase (`"E disse Deus:"`, `"E respondeu-lhe o
  SENHOR:"`, etc.) as its own `narrator` segment, including the trailing
  colon, immediately followed by the speaker's segment(s).
- When a quote continues into a following verse without a new "disse"-style
  marker, don't repeat a narrator lead-in — start that verse directly with
  the speaker segment, and split off any narrator words that resume the
  narration (e.g. `"e foi assim."`) as a trailing segment.
- Strip wrapping curly quotes (`“ ” ‘ ’` and guillemets `« »`) around direct
  speech; the `speaker` field now conveys that, so the raw quote marks are
  redundant. Plain straight quotes should also be stripped when they only
  wrap a full quoted segment.
- Nested quotes (a speaker quoting someone else's earlier words, or quoting
  themselves) are **not** split into an extra segment — keep them under the
  outer speaker.
- Mid-sentence attribution asides like `"(disse ela)"` / `", disse ele,"` are
  dropped entirely (use `"force": true`) rather than kept as their own
  narrator segment, to avoid awkward fragmentation.
- Verses that mention speech happening but don't quote actual words (e.g.
  `"Caim falou a seu irmão Abel"` with no reported words) are left as
  narrator-only — nothing to split.
- Never change wording/spelling of the source text when splitting (verified
  automatically by the script's text-match check); only reposition text
  across segments and strip redundant quote marks/attribution asides.

## Book processing order

Old Testament (folder name → book):

1. genesis (in progress, chapters 6-50 remaining)
2. exodo
3. levitico
4. numeros
5. deuteronomio
6. josue
7. juizes
8. rute
9. 1samuel
10. 2samuel
11. 1reis
12. 2reis
13. 1cronicas
14. 2cronicas
15. esdras
16. neemias
17. ester
18. jo (Jó / Job — not to be confused with `joao`/John)
19. salmos
20. proverbios
21. eclesiastes
22. canticos
23. isaias
24. jeremias
25. lamentacoes
26. ezequiel
27. daniel
28. oseias
29. joel
30. amos
31. obadias
32. jonas
33. miqueias
34. naum
35. habacuque
36. sofonias
37. ageu
38. zacarias
39. malaquias

New Testament:

40. mateus
41. marcos
42. lucas
43. joao
44. atos
45. romanos
46. 1corintios
47. 2corintios
48. galatas
49. efesios
50. filipenses
51. colossenses
52. 1tessalonicenses
53. 2tessalonicenses
54. 1timoteo
55. 2timoteo
56. tito
57. filemom
58. hebreus
59. tiago
60. 1pedro
61. 2pedro
62. 1joao
63. 2joao
64. 3joao
65. judas
66. apocalipse

Books with mostly narrative/dialogue (Genesis, Exodus, Samuel/Kings,
Gospels, Acts) need the most splitting work; epistles are almost entirely a
single speaker (the author) addressing readers directly and rarely need any
split beyond an occasional quoted OT verse or reported saying.

## Progress tracking

Update this section (or repo memory) as books are completed:

- [x] genesis 1-5
- [x] genesis 6-10
- [ ] genesis 11-50
- [ ] exodo
- [ ] ... (rest of Old Testament)
- [ ] ... (New Testament)
