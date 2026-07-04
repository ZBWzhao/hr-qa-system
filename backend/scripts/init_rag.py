"""初始化RAG系统：创建向量数据库并索引所有文档"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.models.qa import QARecord, Rule, QAMiss
from app.services.text_splitter import chunk_document
from app.services.rag.vectorstore import add_documents, delete_document, get_collection_stats


def init_database():
    """创建数据库表"""
    print("初始化数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")


def index_documents():
    """索引所有已发布文档到Chroma"""
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.status == "published").all()
        print(f"\n找到 {len(documents)} 个已发布文档")

        if not documents:
            print("没有已发布的文档，跳过索引")
            return

        for doc in documents:
            print(f"\n处理文档: {doc.title} (ID: {doc.id})")

            # 删除旧索引
            delete_document(doc.id)

            # 获取或创建切片
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()

            if not chunks and doc.content_text:
                print(f"  文档无切片，自动切分...")
                chunk_data = chunk_document(doc.content_text)
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


def show_stats():
    """显示系统统计信息"""
    db = SessionLocal()
    try:
        print("\n===== 系统统计 =====")

        doc_count = db.query(Document).count()
        published_count = db.query(Document).filter(Document.status == "published").count()
        chunk_count = db.query(DocumentChunk).count()
        rule_count = db.query(Rule).filter(Rule.status == 1).count()
        qa_count = db.query(QARecord).count()
        miss_count = db.query(QAMiss).count()

        print(f"文档总数: {doc_count} (已发布: {published_count})")
        print(f"文档切片: {chunk_count}")
        print(f"规则数量: {rule_count}")
        print(f"问答记录: {qa_count}")
        print(f"未命中问题: {miss_count}")

        stats = get_collection_stats()
        print(f"向量数据库: {stats['total_chunks']} 个向量")

    finally:
        db.close()


if __name__ == "__main__":
    print("=== HR Copilot RAG系统初始化 ===\n")

    # 1. 初始化数据库
    init_database()

    # 2. 索引文档
    index_documents()

    # 3. 显示统计
    show_stats()

    print("\n初始化完成!")
