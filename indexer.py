import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import NgramAnalyzer
from whoosh.qparser import QueryParser

INDEX_DIR = "index"

schema = Schema(
    id=ID(stored=True),
    content=TEXT(stored=True, analyzer=NgramAnalyzer(minsize=2))
)


def get_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
        return create_in(INDEX_DIR, schema)
    return open_dir(INDEX_DIR)


def index_doc(doc_id, content):
    ix = get_index()
    with ix.writer() as writer:
        writer.add_document(id=str(doc_id), content=content)


def search(query):
    ix = get_index()
    with ix.searcher() as searcher:
        q = QueryParser("content", ix.schema).parse(query)
        return [r["id"] for r in searcher.search(q)]
