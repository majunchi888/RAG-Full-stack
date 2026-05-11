from vectorstore import vectorstore

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 2,
        "fetch_k": 8,
        "lambda_mult": 0.7
    }
)

def deduplicate_docs(docs):
    seen = set()
    unique_docs = []
    for d in docs:
        key = (d.metadata.get("source"), d.metadata.get("page"))
        if key not in seen:
            seen.add(key)
            unique_docs.append(d)
    return unique_docs
