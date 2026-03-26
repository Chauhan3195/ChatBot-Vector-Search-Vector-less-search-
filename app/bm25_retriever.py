from rank_bm25 import BM25Okapi
from collections import defaultdict
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from langchain_core.documents import Document


class BM25Retriever:
    def __init__(self, documents):
        self.documents = documents
        self.tokenized_corpus = [doc.page_content.split() for doc in documents]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def get_relevant_documents(self, query, k=5):
        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.documents[i] for i in top_indices]
    


class HybridRetriever(BaseRetriever):
    vectorstore: any = Field(...)
    bm25_retriever: BM25Retriever = Field(...)

    def get_relevant_documents(self, query, k=5):
        # Step 1: FAISS results with scores
        vector_docs_with_score = self.vectorstore.similarity_search_with_score(query, k=k)

        # Step 2: BM25 results
        bm25_docs = self.bm25_retriever.get_relevant_documents(query, k=k)

        # Step 3: Combine with weighted scoring
        doc_scores = defaultdict(float)

        # FAISS weight (semantic)
        for doc, score in vector_docs_with_score:
            doc_scores[doc.page_content] += score * 0.7

        # BM25 weight (keyword)
        for doc in bm25_docs:
            doc_scores[doc.page_content] += 0.3

        # Step 4: Rank documents
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # Step 5: Return top documents
        final_docs = []
        seen = set()

        for content, _ in sorted_docs:
            if content not in seen:
                seen.add(content)
                final_docs.append(Document(page_content=content))

            if len(final_docs) == k:
                break

        return final_docs