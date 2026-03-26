from app.rag_modules import (
    DataPreparationModule,
    IndexConstructionModule,
    RetrievalOptimizationModule,
    GenerationIntegrationModule
)

class KnowledgeBaseService:
    def __init__(self, settings):
        self.settings = settings
        self.data_module = DataPreparationModule(settings.data_path)
        self.index_module = IndexConstructionModule(
            model_name=settings.embedding_model,
            index_save_path=settings.index_save_path
        )
        self.retrieval_module = None
        self.generation_module = GenerationIntegrationModule(
            model_name=settings.llm_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )

    def initialize(self):
        self.data_module.load_documents()
        chunks = self.data_module.chunk_documents()

        vectorstore = self.index_module.load_index()
        if vectorstore is None:
            vectorstore = self.index_module.build_vector_index(chunks)
            self.index_module.save_index()

        self.retrieval_module = RetrievalOptimizationModule(vectorstore, chunks)

    def retrieve(self, query: str, filters: dict | None = None, top_k: int | None = None):
        top_k = top_k or self.settings.top_k
        if filters:
            chunks, debug_items = self.retrieval_module.retrieve_with_debug(query, filters=filters, top_k=top_k)
        else:
            chunks, debug_items = self.retrieval_module.retrieve_with_debug(query, filters=None, top_k=top_k)

        parent_docs = self.data_module.get_parent_documents(chunks)
        return chunks, parent_docs, debug_items

    def stats(self):
        return self.data_module.get_statistics()