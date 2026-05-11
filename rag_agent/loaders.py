import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

def load_file(file, temp_path):
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        loader = PyPDFLoader(temp_path)
    elif filename.endswith(".docx"):
        loader = Docx2txtLoader(temp_path)
    else:
        loader = TextLoader(temp_path, encoding="utf-8")

    docs = loader.load()

    for d in docs:
        d.metadata["source"] = file.filename
        d.metadata["page"] = str(d.metadata.get("page", 1))

    os.remove(temp_path)
    return docs
