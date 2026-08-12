from typing import Annotated, TypedDict
from backend.rag_agent.retriever import HybridRetriever
from backend.rag_agent.llm import generate_answer, llm
from backend.rag_agent.database import SessionLocal
from langsmith import Client, traceable

import os
import cohere
from dotenv import load_dotenv

load_dotenv()
co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


# ====================== 2. RAG 机器人 ======================
@traceable
def rag_bot(query: str):
    """只用 Dense 检索（对照组）"""
    db = SessionLocal()
    try:
        retriever = HybridRetriever(db=db, doc_id=["6"])

        # 只调用 dense 检索
        dense_results = retriever._dense_search(query, k=3)   # [(id, score), ...]

        # 取出对应的文本
        doc_map = retriever._get_documents([doc_id for doc_id, _ in dense_results])
        docs = [
            {"id": doc_id, "score": score, "content": doc_map[doc_id]}
            for doc_id, score in dense_results
        ]

        context = "\n\n".join([doc["content"] for doc in docs])
        answer = generate_answer(query, context)

        return {
            "answer": answer,
            "documents": [{"page_content": doc["content"]} for doc in docs]
        }
    finally:
        db.close()

#     """混合检索：BM25 + Dense + RRF + Rerank"""
# def rag_bot(query: str):

#     db = SessionLocal()
#     try:
#         retriever = HybridRetriever(db=db, doc_id=[6])
    
#         docs = retriever.search(query, k=3)
    
#         context = "\n\n".join([doc["content"] for doc in docs])
    
#         answer = generate_answer(query, context)
    
#         return {"answer": answer, "documents": [{"page_content": doc["content"]} for doc in docs]}

#     finally:
#         db.close()

# ====================== 4. 四个评估器（中文提示词）======================
class CorrectnessGrade(TypedDict):
    explanation: Annotated[str, ..., "评分理由"]
    correct: Annotated[bool, ..., "答案是否正确"]

correctness_instructions = """你是一名阅卷老师。
你会得到一个问题、标准答案和学生的回答。

评分标准：
1. 只根据学生回答与标准答案的事实一致性来判断。
2. 学生回答不能包含与标准答案冲突的内容。
3. 学生回答可以比标准答案更详细，只要事实正确即可。

请一步步思考，最后只返回如下 JSON：
{
  "explanation": "你的推理过程",
  "correct": true 或 false
}"""

correctness_llm = llm.with_structured_output(CorrectnessGrade, method="json_schema", strict=True)

def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    answers = f"""问题：{inputs['question']}
标准答案：{reference_outputs['answer']}
学生回答：{outputs['answer']}"""
    grade = correctness_llm.invoke([
        {"role": "system", "content": correctness_instructions},
        {"role": "user", "content": answers}
    ])
    return grade["correct"]


class RelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "评分理由"]
    relevant: Annotated[bool, ..., "回答是否与问题相关"]

relevance_instructions = """你是一名阅卷老师。
你会得到一个问题和学生的回答。

评分标准：
1. 回答必须简洁且与问题相关。
2. 回答必须有助于解决该问题。

请一步步思考，最后只返回如下 JSON：
{
  "explanation": "你的推理过程",
  "relevant": true 或 false
}"""

relevance_llm = llm.with_structured_output(RelevanceGrade, method="json_mode")

def relevance(inputs: dict, outputs: dict) -> bool:
    answer = f"问题：{inputs['question']}\n学生回答：{outputs['answer']}"
    grade = relevance_llm.invoke([
        {"role": "system", "content": relevance_instructions},
        {"role": "user", "content": answer}
    ])
    return grade["relevant"]


class GroundedGrade(TypedDict):
    explanation: Annotated[str, ..., "评分理由"]
    grounded: Annotated[bool, ..., "回答是否基于提供的文档，没有幻觉"]

grounded_instructions = """你是一名阅卷老师。
你会得到参考事实和学生的回答。

评分标准：
1. 学生回答必须基于提供的事实。
2. 不能出现事实中没有的“幻觉”内容。

请一步步思考，最后只返回如下 JSON：
{
  "explanation": "你的推理过程",
  "grounded": true 或 false
}"""

grounded_llm = llm.with_structured_output(GroundedGrade, method="json_mode")

def groundedness(inputs: dict, outputs: dict) -> bool:
    doc_string = "\n\n".join(doc["page_content"] for doc in outputs["documents"])
    answer = f"参考事实：{doc_string}\n学生回答：{outputs['answer']}"
    grade = grounded_llm.invoke([
        {"role": "system", "content": grounded_instructions},
        {"role": "user", "content": answer}
    ])
    return grade["grounded"]


class RetrievalRelevanceGrade(TypedDict):
    explanation: Annotated[str, ..., "评分理由"]
    relevant: Annotated[bool, ..., "检索到的文档是否与问题相关"]

retrieval_relevance_instructions = """你是一名阅卷老师。
你会得到一个问题和一组检索到的事实。

评分标准：
1. 目标是找出与问题完全无关的事实。
2. 只要事实中包含与问题相关的关键词或语义，就视为相关。
3. 即使有部分无关内容，只要满足第2点也算相关。

请一步步思考，最后只返回如下 JSON：
{
  "explanation": "你的推理过程",
  "relevant": true 或 false
}"""

retrieval_relevance_llm = llm.with_structured_output(RetrievalRelevanceGrade, method="json_mode")

def retrieval_relevance(inputs: dict, outputs: dict) -> bool:
    doc_string = "\n\n".join(doc["page_content"] for doc in outputs["documents"])
    answer = f"检索到的事实：{doc_string}\n问题：{inputs['question']}"
    grade = retrieval_relevance_llm.invoke([
        {"role": "system", "content": retrieval_relevance_instructions},
        {"role": "user", "content": answer}
    ])
    return grade["relevant"]


# ====================== 5. 创建数据集并运行评估 ======================
examples = [
    {
        "inputs": {"question": "什么是RAG？"},
        "outputs": {"answer": "RAG是检索增强生成（Retrieval-Augmented Generation），通过先检索相关文档，再将文档内容作为上下文提供给大语言模型来生成回答。"}
    },
    {
        "inputs": {"question": "RAG的核心价值是什么？"},
        "outputs": {"answer": "解决大模型知识截止和幻觉问题，支持私有知识和实时知识接入，提高回答的可追溯性和可控性。"}
    },
    {
        "inputs": {"question": "标准RAG流水线包含哪些主要步骤？"},
        "outputs": {"answer": "文档解析与切分、向量化并建立索引、检索、（可选）重排序、将上下文与问题送给LLM生成答案、（可选）评估。"}
    },
    {
        "inputs": {"question": "Dense Retrieval是什么？它有什么优缺点？"},
        "outputs": {"answer": "Dense Retrieval使用向量嵌入模型将查询和文档映射到同一语义空间，通过相似度计算相关性。优点是能捕捉语义相似性、对同义词鲁棒；缺点是对关键词精确匹配较弱，且依赖高质量embedding模型。"}
    },
    {
        "inputs": {"question": "BM25属于什么类型的检索？它的优缺点是什么？"},
        "outputs": {"answer": "BM25属于稀疏检索（Sparse Retrieval）。优点是关键词匹配精确、可解释性强、无需训练；缺点是难以处理语义相近但用词不同的情况。"}
    },
    {
        "inputs": {"question": "什么是混合检索？"},
        "outputs": {"answer": "混合检索同时使用Dense和Sparse两种检索方式，再通过融合算法合并结果，实践中能显著提升召回率和最终回答质量。"}
    },
    {
        "inputs": {"question": "RRF的全称是什么？它的核心思想是什么？"},
        "outputs": {"answer": "RRF全称是Reciprocal Rank Fusion。它只使用排名信息而非原始分数进行融合，对异构检索器非常友好。"}
    },
    {
        "inputs": {"question": "RRF的计算公式是什么？k通常取多少？"},
        "outputs": {"answer": "score(d) = Σ 1 / (k + rank_i(d))，其中k通常取60。"}
    },
    {
        "inputs": {"question": "为什么RRF适合融合Dense和BM25的结果？"},
        "outputs": {"answer": "因为RRF只依赖排名而不依赖原始分数的尺度，能够有效融合分数分布不同的异构检索器结果。"}
    },
    {
        "inputs": {"question": "Rerank的作用是什么？"},
        "outputs": {"answer": "在召回阶段获得候选文档后，使用更强的交叉编码器模型对查询-文档对进行精细打分并重新排序，从而提升Top-K结果的精度。"}
    },
    {
        "inputs": {"question": "常见的Rerank模型有哪些？"},
        "outputs": {"answer": "常见模型包括Cohere Rerank、bge-reranker、Jina Reranker等。"}
    },
    {
        "inputs": {"question": "在RAG中，Correctness指标衡量什么？"},
        "outputs": {"answer": "Correctness衡量生成答案是否与参考答案语义一致、事实正确。"}
    },
    {
        "inputs": {"question": "Groundedness指标是什么意思？"},
        "outputs": {"answer": "Groundedness（忠实性）衡量答案是否严格基于检索到的上下文，没有凭空捏造。"}
    },
    {
        "inputs": {"question": "Retrieval Relevance指标评估什么？"},
        "outputs": {"answer": "Retrieval Relevance评估检索到的文档是否真正与问题相关。"}
    },
    {
        "inputs": {"question": "为什么混合检索通常比单一Dense检索效果更好？"},
        "outputs": {"answer": "Dense擅长语义匹配，BM25擅长关键词匹配，两者互补，通过RRF融合能有效结合双方优势。"}
    },
    {
        "inputs": {"question": "召回阶段的candidate_k建议设置为最终k的多少倍？"},
        "outputs": {"answer": "建议设为最终k的3到5倍。"}
    },
    {
        "inputs": {"question": "加入Rerank后通常哪个指标提升最明显？"},
        "outputs": {"answer": "加入Rerank后Top-K（尤其是Top-5）精度提升最为显著。"}
    },
    {
        "inputs": {"question": "如何量化评估检索链路是否有效？"},
        "outputs": {"answer": "通过correctness、groundedness、retrieval relevance等指标进行量化对比，而不是仅凭主观感受。"}
    },
    {
        "inputs": {"question": "LangSmith在RAG评测中可以做什么？"},
        "outputs": {"answer": "使用LangSmith可构建自动化评测体系，记录traces和评估结果，对比不同检索策略的指标变化，便于实验管理和面试展示。"}
    },
    {
        "inputs": {"question": "RAG如何帮助解决大模型的幻觉问题？"},
        "outputs": {"answer": "通过先检索相关文档并将文档内容作为上下文提供给大模型，使生成内容有据可依，从而减少幻觉。"}
    },
    {
        "inputs": {"question": "Dense Retrieval对同义词的处理能力如何？"},
        "outputs": {"answer": "Dense Retrieval能较好捕捉语义相似性，对同义词和改写较为鲁棒。"}
    },
    {
        "inputs": {"question": "BM25是否需要训练？"},
        "outputs": {"answer": "BM25不需要训练，是基于词频统计的经典算法。"}
    },
    {
        "inputs": {"question": "混合检索的主要优势是什么？"},
        "outputs": {"answer": "能够结合Dense的语义能力和BM25的关键词精确匹配能力，显著提升召回率和最终回答质量。"}
    },
    {
        "inputs": {"question": "RRF中的k参数起什么作用？"},
        "outputs": {"answer": "k是一个平滑参数，用于降低排名靠后文档的权重，通常取值为60。"}
    },
    {
        "inputs": {"question": "Rerank为什么比单纯的向量相似度更准确？"},
        "outputs": {"answer": "Rerank使用交叉编码器对查询和文档进行联合编码和打分，能捕捉更细粒度的交互信息，因此精度更高。"}
    },
    {
        "inputs": {"question": "在延迟敏感的场景下是否必须使用Rerank？"},
        "outputs": {"answer": "不一定。如果延迟敏感且候选质量已经很高，可以关闭Rerank。"}
    },
    {
        "inputs": {"question": "构建RAG测试集时建议包含哪些类型的问题？"},
        "outputs": {"answer": "建议覆盖事实型、对比型、多跳推理等不同类型的问题。"}
    },
    {
        "inputs": {"question": "建议的测试集规模是多少？"},
        "outputs": {"answer": "建议构建20到50条高质量测试集。"}
    },
    {
        "inputs": {"question": "Context Precision和Context Recall分别衡量什么？"},
        "outputs": {"answer": "Context Precision衡量检索上下文的精确率，Context Recall衡量检索上下文的召回率。"}
    },
    {
        "inputs": {"question": "RAG流水线中的Chunking是指什么？"},
        "outputs": {"answer": "Chunking是指对文档进行解析和切分，将长文档分成适合检索和嵌入的小片段。"}
    },
    {
        "inputs": {"question": "为什么说RRF对异构检索器友好？"},
        "outputs": {"answer": "因为RRF只使用排名信息，不依赖各检索器原始分数的绝对数值和尺度，因此能自然融合不同类型的检索结果。"}
    },
    {
        "inputs": {"question": "仅使用Dense Retrieval有什么主要局限？"},
        "outputs": {"answer": "对关键词精确匹配能力较弱，可能漏掉包含重要专有名词或精确术语的文档。"}
    },
    {
        "inputs": {"question": "仅使用BM25有什么主要局限？"},
        "outputs": {"answer": "难以处理语义相近但用词不同的查询，对同义词和改写不敏感。"}
    },
    {
        "inputs": {"question": "生产级RAG为什么常把Rerank作为标配？"},
        "outputs": {"answer": "因为Rerank能显著提升Top-K结果的精度，对最终回答质量影响很大。"}
    },
    {
        "inputs": {"question": "如何通过实验证明混合检索+Rerank的有效性？"},
        "outputs": {"answer": "对比仅Dense检索与BM25+Dense+RRF+Rerank两种策略在correctness等指标上的表现，量化准确率提升幅度。"}
    },
    {
        "inputs": {"question": "RAG中检索到的文档如何被使用？"},
        "outputs": {"answer": "检索到的文档片段会作为上下文与用户问题一起提供给大语言模型，用于生成回答。"}
    },
    {
        "inputs": {"question": "什么是交叉编码器（Cross-Encoder）？"},
        "outputs": {"answer": "交叉编码器是一种将查询和文档拼接后共同编码并输出相关性分数的模型，常用于Rerank阶段。"}
    },
    {
        "inputs": {"question": "在RAG评测中，为什么不能只看主观感受？"},
        "outputs": {"answer": "主观感受难以量化且不稳定，应通过correctness、groundedness、retrieval relevance等客观指标进行系统对比。"}
    },
    {
        "inputs": {"question": "混合检索中双路召回后通常还需要什么步骤？"},
        "outputs": {"answer": "双路召回后通常使用RRF等算法进行结果融合，然后再进行Rerank。"}
    },
    {
        "inputs": {"question": "Rerank的输入是什么？"},
        "outputs": {"answer": "Rerank的输入是查询以及召回阶段得到的候选文档列表。"}
    },
    {
        "inputs": {"question": "文档中提到的embedding模型主要用于什么阶段？"},
        "outputs": {"answer": "主要用于Dense Retrieval阶段，将查询和文档映射到向量空间。"}
    },
    {
        "inputs": {"question": "为什么说RAG能支持私有知识接入？"},
        "outputs": {"answer": "因为RAG可以从外部私有知识库中检索相关内容，再提供给大模型，无需将私有数据直接训练进模型。"}
    },
    {
        "inputs": {"question": "RRF融合时使用的是原始分数还是排名？"},
        "outputs": {"answer": "RRF只使用排名信息，不使用原始分数。"}
    },
    {
        "inputs": {"question": "提升RAG回答准确率的有效手段有哪些？"},
        "outputs": {"answer": "采用混合检索（BM25+Dense）、使用RRF融合、加入Rerank、构建高质量测试集并用指标量化优化效果。"}
    },
    {
        "inputs": {"question": "在简历中如何体现RAG优化成果更有说服力？"},
        "outputs": {"answer": "使用LangSmith构建自动化评测体系，通过correctness等指标对比优化前后的提升幅度，并保存实验记录和截图。"}
    },
    {
        "inputs": {"question": "候选文档数量candidate_k和最终返回数量k的关系是什么？"},
        "outputs": {"answer": "candidate_k通常大于k，建议设为k的3到5倍，以便后续Rerank有足够候选进行精排。"}
    },
    {
        "inputs": {"question": "Groundedness低通常说明什么问题？"},
        "outputs": {"answer": "说明模型生成的内容没有很好地基于检索到的上下文，可能存在幻觉或过度发挥。"}
    },
    {
        "inputs": {"question": "Retrieval Relevance低通常说明什么问题？"},
        "outputs": {"answer": "说明检索阶段返回的文档与用户问题相关性不足，需要优化检索策略或索引质量。"}
    },
    {
        "inputs": {"question": "完整的推荐检索链路是什么？"},
        "outputs": {"answer": "BM25与Dense双路召回 → RRF融合 → Rerank精排 → 将Top-K文档作为上下文送给LLM生成答案。"}
    },
    {
        "inputs": {"question": "为什么建议保存LangSmith的评测截图？"},
        "outputs": {"answer": "方便在面试中展示优化前后的指标对比和完整实验过程，增强说服力。"}
    }
]

if __name__ == "__main__":
    client = Client()

    dataset_name = "RAG中文检索评估集"

    # 如果数据集已存在就直接用，否则创建
    try:
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"使用已有数据集: {dataset_name}")
    except Exception:
        dataset = client.create_dataset(dataset_name=dataset_name)
        client.create_examples(dataset_id=dataset.id, examples=examples)
        print(f"已创建数据集: {dataset_name}")

    def target(inputs: dict) -> dict:
        return rag_bot(inputs["question"])

    print("开始评估...")
    experiment_results = client.evaluate(
        target,
        data=dataset_name,
        evaluators=[correctness, relevance, groundedness, retrieval_relevance], 
        experiment_prefix="rag-hybrid-bge-m3",
        metadata={"version": "Only dense + BGE-M3 + RRF"}
    )

    print("\n评估完成！结果预览：")
    print(experiment_results.to_pandas())