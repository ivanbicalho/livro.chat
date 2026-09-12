const BOOKS = {};
const CHARACTERS = {};

// fetched once on app startup
const initPromise = fetch('api/pt-br/blivre/init.json')
    .then((res) => res.json())
    .then((data) => {
        (data.books || []).forEach((book) => { BOOKS[book.api] = book; });
        (data.characters || []).forEach((character) => { CHARACTERS[character.id] = character; });
    });

function characterFor(speakerId) {
    return CHARACTERS[speakerId] || { id: speakerId, name: speakerId, icon: '' };
}

function buildMessages(verses) {
    const messages = [];
    verses.forEach((verseEntry) => {
        verseEntry.segments.forEach((segment, index) => {
            const character = characterFor(segment.speaker);
            messages.push({
                id: `${verseEntry.verse}-${index}`,
                verse: verseEntry.verse,
                text: segment.text,
                name: character.name,
                icon: character.icon ? `img/${character.icon}` : '',
                side: segment.speaker === 'narrator' ? 'left' : 'right',
            });
        });
    });
    return messages;
}

async function loadChapter(book, chapter) {
    const store = Alpine.store('chat');
    store.loading = true;
    store.error = null;
    try {
        await initPromise;
        const res = await fetch(`api/pt-br/blivre/${book}/${chapter}.json`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        store.name = data.name;
        store.chapter = data.chapter;
        store.book = data.book;
        store.messages = buildMessages(data.verses);
    } catch (err) {
        store.error = 'Não foi possível carregar este capítulo.';
        store.messages = [];
    } finally {
        store.loading = false;
    }
}

document.addEventListener('alpine:init', () => {
    Alpine.store('chat', {
        name: '',
        book: null,
        chapter: null,
        messages: [],
        loading: true,
        error: null,
    });

    const router = new Navigo('/', { hash: true });
    router
        .on('/:book/:chapter', ({ data }) => loadChapter(data.book, data.chapter))
        .notFound(() => router.navigate('/genesis/1'))
        .resolve();

    if (!window.location.hash || window.location.hash === '#/') {
        router.navigate('/genesis/1');
    }
});
