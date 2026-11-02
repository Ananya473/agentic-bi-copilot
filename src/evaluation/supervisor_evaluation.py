
from src.agents.supervisor import plan_agents


# Expected agent selections are manually defined
# and serve as our evaluation ground truth.

EVALUATION_DATASET = [
    {
        "question": "What is the total revenue?",
        "expected": {"data_analyst"},
    },
    {
        "question": "Which five products generate the most revenue?",
        "expected": {"data_analyst"},
    },
    {
        "question": "Why did revenue decline last month?",
        "expected": {"data_analyst", "investigator"},
    },
    {
        "question": "Compare monthly sales performance.",
        "expected": {"data_analyst", "investigator"},
    },
    {
        "question": "Explain our return policy.",
        "expected": {"knowledge_researcher"},
    },
    {
        "question": "How do promotional campaigns affect customer behaviour?",
        "expected": {"knowledge_researcher"},
    },
    {
        "question": "Are there unusual spikes in daily revenue?",
        "expected": {"data_analyst", "investigator"},
    },
    {
        "question": "Which countries have the highest sales?",
        "expected": {"data_analyst"},
    },
    {
        "question": "How does inventory management handle out-of-stock products?",
        "expected": {"knowledge_researcher"},
    },
    {
        "question": (
            "Analyze revenue decline and check whether "
            "promotions could explain it."
        ),
        "expected": {
            "data_analyst",
            "investigator",
            "knowledge_researcher",
        },
    },
]


def evaluate_supervisor():
    total_exact_matches = 0

    true_positive = 0
    false_positive = 0
    false_negative = 0

    results = []

    print("\nSUPERVISOR AGENT EVALUATION")
    print("=" * 65)

    for index, case in enumerate(EVALUATION_DATASET, start=1):

        question = case["question"]
        expected = case["expected"]

        try:
            plan = plan_agents(question)

            actual = {
                item["agent"]
                for item in plan["agents"]
            }

            source = plan["source"]

            correct = expected & actual
            incorrect = actual - expected
            missed = expected - actual

            exact_match = expected == actual

            if exact_match:
                total_exact_matches += 1

            true_positive += len(correct)
            false_positive += len(incorrect)
            false_negative += len(missed)

            results.append({
                "question": question,
                "expected": expected,
                "actual": actual,
                "source": source,
                "exact_match": exact_match,
            })

            print(f"\nTest {index}")
            print(f"Question: {question}")
            print(f"Expected: {sorted(expected)}")
            print(f"Selected: {sorted(actual)}")
            print(f"Planning method: {source}")
            print(f"Exact match: {exact_match}")

            if missed:
                print(f"Missing agents: {sorted(missed)}")

            if incorrect:
                print(f"Extra agents: {sorted(incorrect)}")

        except Exception as error:
            print(f"\nTest {index} failed: {error}")

            false_negative += len(expected)

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    accuracy = total_exact_matches / len(EVALUATION_DATASET)

    print("\n" + "=" * 65)
    print("FINAL EVALUATION RESULTS")
    print("=" * 65)

    print(f"Total questions: {len(EVALUATION_DATASET)}")
    print(f"Exact matches: {total_exact_matches}")
    print(f"Exact-match accuracy: {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1-score: {f1_score:.2%}")

    print("=" * 65)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "results": results,
    }


if __name__ == "__main__":
    evaluate_supervisor()
