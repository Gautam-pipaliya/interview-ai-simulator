from .language import localize_feedback, normalize_language


PROGRAMMING_LANGUAGES = {
    "python": {
        "label": "Python",
        "mode": "python",
        "mime": "text/x-python",
        "can_run": False,
    },
    "javascript": {
        "label": "JavaScript",
        "mode": "javascript",
        "mime": "text/javascript",
        "can_run": True,
    },
    "java": {
        "label": "Java",
        "mode": "clike",
        "mime": "text/x-java",
        "can_run": False,
    },
    "cpp": {
        "label": "C++",
        "mode": "clike",
        "mime": "text/x-c++src",
        "can_run": False,
    },
}


STARTER_SNIPPETS = {
    "python": """def solve(nums):
    # Write your solution here
    return None


print(solve([2, 7, 11, 15]))
""",
    "javascript": """function solve(nums) {
  // Write your solution here
  return null;
}

console.log(solve([2, 7, 11, 15]));
""",
    "java": """class Solution {
    public static Object solve(int[] nums) {
        // Write your solution here
        return null;
    }
}
""",
    "cpp": """#include <bits/stdc++.h>
using namespace std;

auto solve(vector<int> nums) {
    // Write your solution here
    return 0;
}
""",
}


def get_programming_languages():
    return [
        {
            "key": key,
            "label": payload["label"],
            "mode": payload["mode"],
            "mime": payload["mime"],
            "can_run": payload["can_run"],
        }
        for key, payload in PROGRAMMING_LANGUAGES.items()
    ]


def normalize_programming_language(value):
    candidate = str(value or "python").strip().lower()
    return candidate if candidate in PROGRAMMING_LANGUAGES else "python"


def get_starter_code(language):
    return STARTER_SNIPPETS[normalize_programming_language(language)]


def evaluate_code_submission(code, ideal_answer, language_code="en"):
    code_text = str(code or "").strip()
    if not code_text:
        return localize_feedback(
            {
                "score": 0.0,
                "feedback": "No code submitted. Add a solution before submitting the round.",
                "missing_keywords": ["solution", "logic", "edge cases"],
            },
            language_code,
        )

    lowered = code_text.lower()
    score = 35.0

    if any(token in lowered for token in ["def ", "function ", "class ", "public static", "auto solve", "int main"]):
        score += 18.0
    if any(token in lowered for token in ["for ", "while ", ".map", ".reduce", "stream", "foreach"]):
        score += 14.0
    if any(token in lowered for token in ["if ", "else", "switch", "case"]):
        score += 12.0
    if any(token in lowered for token in ["return", "print", "console.log", "system.out", "cout"]):
        score += 8.0
    if any(token in lowered for token in ["null", "none", "empty", "edge", "length", "size", "len("]):
        score += 6.0
    if len(code_text.splitlines()) >= 8:
        score += 7.0

    score = round(min(score, 100.0), 2)
    missing = []
    if not any(token in lowered for token in ["if ", "else", "switch", "case"]):
        missing.append("edge cases")
    if not any(token in lowered for token in ["for ", "while ", ".map", ".reduce", "foreach"]):
        missing.append("iteration")
    if "return" not in lowered:
        missing.append("return value")

    feedback = (
        "Code submitted. The evaluator checked structure, control flow, return behavior, and edge-case signals. "
        "Use the browser run panel for JavaScript output and review the expected approach below."
    )
    if ideal_answer:
        feedback += f" Expected approach: {ideal_answer}"

    return localize_feedback(
        {
            "score": score,
            "feedback": feedback,
            "missing_keywords": missing,
        },
        normalize_language(language_code),
    )
