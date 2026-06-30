from docx import Document
doc = Document('HR制度智能问答系统_需求分析文档_V3.0.docx')
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)
