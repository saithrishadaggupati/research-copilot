"""
Ragas Evaluation for Research Copilot
Metrics: Faithfulness, Answer Relevance, Context Recall
Run: python evals/eval_research.py
"""
import json
import requests
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

API_URL = "http://localhost:8000/api/v1/research"

EVAL_DATASET = [
    {"question": "What is retrieval-augmented generation?", "ground_truth": "RAG is a technique that combines information retrieval with language model generation to improve accuracy."},
    {"question": "What is the difference between RAG and fine-tuning?", "ground_truth": "RAG retrieves external knowledge at inference time while fine-tuning updates model weights during training."},
    {"question": "What is LangChain?", "ground_truth": "LangChain is a framework for building applications with large language models."},
    {"question": "What is a vector database?", "ground_truth": "A vector database stores high-dimensional embeddings and enables similarity search."},
    {"question": "What is prompt engineering?", "ground_truth": "Prompt engineering is the practice of designing inputs to guide language model outputs."},
]

def run_eval():
    questions, answers, contexts, ground_truths = [], [], [], []

    print("Running queries against Research Copilot...")
    for item in EVAL_DATASET:
        try:
            response = requests.post(API_URL, json={
                "query": item["question"],
                "max_results": 5,
                "use_web_search": True
            }, timeout=60)

            if response.status_code == 200:
                data = response.json()
                questions.append(item["question"])
                answers.append(data["answer"])
                contexts.append([s["content"] for s in data["sources"]])
                ground_truths.append(item["ground_truth"])
                print(f"  [OK] {item['question'][:50]}...")
            else:
                print(f"  [FAIL] {item['question'][:50]} - {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    if not questions:
        print("No results collected. Is the backend running?")
        return

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    print("\nRunning Ragas evaluation...")
    results = evaluate(dataset, metrics=[faithfulness, answer_relevancy])

    print("\n=== Ragas Evaluation Results ===")
    print(f"Faithfulness:     {results['faithfulness']:.4f}")
    print(f"Answer Relevancy: {results['answer_relevancy']:.4f}")

    with open("evals/results.json", "w") as f:
        json.dump({
            "faithfulness": results["faithfulness"],
            "answer_relevancy": results["answer_relevancy"],
            "num_samples": len(questions)
        }, f, indent=2)

    print("\nResults saved to evals/results.json")

if __name__ == "__main__":
    run_eval()
