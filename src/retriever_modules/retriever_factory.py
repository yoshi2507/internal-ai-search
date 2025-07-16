# src/components/retriever_factory.py

from typing import List, Optional, Dict
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.base import VectorStoreRetriever
from langchain_core.documents import Document


def build_employee_retriever(
    db_path: Optional[str] = None,
    filter_conditions: Optional[Dict] = None,
    k: int = 5,
    docs: Optional[List[Document]] = None,
    embeddings: Optional[OpenAIEmbeddings] = None
) -> VectorStoreRetriever:
    """
    社員名簿ベースのretrieverを構築（from_documents or from_persisted_db 両対応）
    """
    if embeddings is None:
        embeddings = OpenAIEmbeddings()

    if docs:
        vectordb = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_metadata={"category": "employee"}
        )
    elif db_path:
        vectordb = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )
    else:
        raise ValueError("docs も db_path も指定されていません")

    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    
    if filter_conditions:
        retriever.search_kwargs["filter"] = filter_conditions

    return retriever