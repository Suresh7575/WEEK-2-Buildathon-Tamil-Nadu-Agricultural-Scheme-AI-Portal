
from src.rag import answer_question_stream


def run_evaluation():

    test_questions = [
        {
            "question": "What is the subsidy for general category farmers?",
            "expected": "50%"
        },
        {
            "question": "What is the maximum subsidy ceiling for SC farmers?",
            "expected": "5 lakhs"
        },
        {
            "question": "What is the exact last date to apply in 2026?",
            "expected": "not available"
        }
    ]

    print("\nAGRICULTURAL SCHEME AI - EVALUATION")
    print("=" * 50)

    passed = 0
    failed = 0

    for index, test in enumerate(test_questions, start=1):

        print(f"\nTest {index}: {test['question']}")

        answer = answer_question_stream(
            test["question"],
            chat_history=[]
        )

        if test["expected"].lower() in answer.lower():

            print("\nResult: PASSED")
            passed += 1

        else:

            print("\nResult: FAILED")
            print("Expected:", test["expected"])
            failed += 1

    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("Total tests:", len(test_questions))
    print("Passed:", passed)
    print("Failed:", failed)

    print("\nSTEP 19 EVALUATION COMPLETED")


if __name__ == "__main__":
    run_evaluation()
