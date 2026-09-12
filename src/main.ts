import "./style.css";
import Alpine from "alpinejs";
import Navigo from "navigo";

interface Book {
  api: string;
  [key: string]: unknown;
}

interface Character {
  id: string;
  name: string;
  icon: string;
}

interface Segment {
  speaker: string;
  text: string;
}

interface VerseEntry {
  verse: number;
  segments: Segment[];
}

interface ChapterResponse {
  name: string;
  chapter: number;
  book: string;
  verses: VerseEntry[];
}

interface Message {
  id: string;
  verse: number;
  text: string;
  name: string;
  icon: string;
  side: "left" | "right";
}

interface ChatStore {
  name: string;
  book: string | null;
  chapter: number | null;
  messages: Message[];
  loading: boolean;
  error: string | null;
}

declare global {
  interface Window {
    Alpine: typeof Alpine;
  }
}

const BOOKS: Record<string, Book> = {};
const CHARACTERS: Record<string, Character> = {};

// fetched once on app startup
const initPromise = fetch("/api/pt-br/blivre/init.json")
  .then((res) => res.json())
  .then((data) => {
    (data.books || []).forEach((book: Book) => {
      BOOKS[book.api] = book;
    });
    (data.characters || []).forEach((character: Character) => {
      CHARACTERS[character.id] = character;
    });
  });

function characterFor(speakerId: string): Character {
  return CHARACTERS[speakerId] || { id: speakerId, name: speakerId, icon: "" };
}

function buildMessages(verses: VerseEntry[]): Message[] {
  const messages: Message[] = [];
  verses.forEach((verseEntry) => {
    verseEntry.segments.forEach((segment, index) => {
      const character = characterFor(segment.speaker);
      messages.push({
        id: `${verseEntry.verse}-${index}`,
        verse: verseEntry.verse,
        text: segment.text,
        name: character.name,
        icon: character.icon ? `/img/${character.icon}` : "",
        side: segment.speaker === "narrator" ? "left" : "right",
      });
    });
  });
  return messages;
}

async function loadChapter(book: string, chapter: string) {
  const store = Alpine.store("chat") as unknown as ChatStore;
  store.loading = true;
  store.error = null;
  try {
    await initPromise;
    const res = await fetch(`/api/pt-br/blivre/${book}/${chapter}.json`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: ChapterResponse = await res.json();
    store.name = data.name;
    store.chapter = data.chapter;
    store.book = data.book;
    store.messages = buildMessages(data.verses);
  } catch (err) {
    store.error = "Não foi possível carregar este capítulo.";
    store.messages = [];
  } finally {
    store.loading = false;
  }
}

document.addEventListener("alpine:init", () => {
  Alpine.store("chat", {
    name: "",
    book: null,
    chapter: null,
    messages: [],
    loading: true,
    error: null,
  } satisfies ChatStore);

  const router = new Navigo("/", { hash: true });
  router
    .on("/:book/:chapter", (match) => {
      const { book, chapter } = match!.data!;
      loadChapter(book, chapter);
    })
    .notFound(() => router.navigate("/genesis/1"))
    .resolve();

  if (!window.location.hash || window.location.hash === "#/") {
    router.navigate("/genesis/1");
  }
});

window.Alpine = Alpine;
Alpine.start();
