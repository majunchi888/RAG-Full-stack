
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

def load_file(temp_path: str):
    """
    传入本地临时文件路径，返回Document列表
    不再接收UploadFile对象，文件删除交给调用方finally处理
    """
    # 从路径拿到原始文件名
    file_path = Path(temp_path)
    original_filename = file_path.name
    # 剥离uuid前缀，还原真实文件名（你的临时文件格式 temp_uuid_xxx.pdf）
    if "_" in original_filename:
        original_filename = "_".join(original_filename.split("_")[2:])
    filename = original_filename.lower()

    if filename.endswith(".pdf"):
        loader = PyPDFLoader(temp_path)
    elif filename.endswith(".docx"):
        loader = Docx2txtLoader(temp_path)
    else:
        # 兼容windows中文gbk，自动尝试编码
        try:
            loader = TextLoader(temp_path, encoding="utf-8")
        except UnicodeDecodeError:
            loader = TextLoader(temp_path, encoding="gbk")

    docs = loader.load()

    for d in docs:
        d.metadata["source"] = original_filename
        d.metadata["page"] = str(d.metadata.get("page", 1))

    # ❗删掉这里os.remove(temp_path)，由上层upload接口的finally删除临时文件
    return docs

