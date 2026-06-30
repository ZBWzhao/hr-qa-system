"""将数据库中的文档索引到Chroma向量数据库"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.text_splitter import chunk_document
from app.services.rag.vectorstore import add_documents, delete_document, get_collection_stats


def index_all_documents():
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.status == "published").all()
        print(f"找到 {len(documents)} 个已发布文档")

        for doc in documents:
            print(f"处理文档: {doc.title} (ID: {doc.id})")

            delete_document(doc.id)

            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()

            if not chunks and doc.content:
                print(f"  文档无切片，自动切分...")
                chunk_data = chunk_document(doc.content)
                for i, cd in enumerate(chunk_data):
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        content=cd["content"],
                        keywords=cd["keywords"],
                        chunk_index=i
                    )
                    db.add(chunk)
                db.commit()
                chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()

            if chunks:
                chunk_dicts = [{"content": c.content, "keywords": c.keywords or ""} for c in chunks]
                add_documents(doc.id, chunk_dicts)
                print(f"  已索引 {len(chunks)} 个切片")
            else:
                print(f"  文档无内容，跳过")

        stats = get_collection_stats()
        print(f"\n索引完成! Chroma中共有 {stats['total_chunks']} 个向量")

    finally:
        db.close()


if __name__ == "__main__":
    index_all_documents()
