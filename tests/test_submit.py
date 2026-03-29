# tests/test_submit.py
import requests

BASE = "http://127.0.0.1:8000"

# First get the questions
questions = requests.get(f"{BASE}/assessment/questions").json()["questions"]
print(f"Got {len(questions)} questions")
print(requests.get(f"{BASE}/assessment/questions").json())
# Build mock answers for all questions
mock_answers = [
    {
        "question_id": q["id"],
        "answer": "test answer",
        "response_time": 5.0
    }
    for q in questions
]

# Submit assessment
payload = {
    "user_id": 1,
    "answers": mock_answers
}

resp = requests.post(f"{BASE}/assessment/submit", json=payload)

print("\nStatus code:", resp.status_code)

if resp.status_code == 200:
    data = resp.json()
    print("Score:",         data.get("score"))
    print("Base band:",     data.get("score_classification"))
    print("Model outputs:", data.get("model_probabilities"))
    print("Final label:",   data.get("classification"))
    print("Decision:",      data.get("decision"))
else:
    print("ERROR:", resp.text)
