from __future__ import annotations

import argparse
import json
import pickle
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Question:
    id: int
    question: str
    type: str  # "mcq" or "short"
    difficulty: str
    topic: str
    tags: List[str]
    explanation: str
    choices: Optional[List[str]] = None
    correct: Optional[int] = None
    answer: Optional[str] = None


@dataclass
class QuestionBank:
    questions: List[Question] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str) -> "QuestionBank":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        qs = [Question(**q) for q in data.get("questions", [])]
        return cls(qs)

    def to_json(self, path: str) -> None:
        data = {"questions": [q.__dict__ for q in self.questions]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def filter(
        self, topic: Optional[str] = None, difficulty: Optional[str] = None
    ) -> List[Question]:
        result = self.questions
        if topic:
            result = [q for q in result if q.topic == topic]
        if difficulty:
            result = [q for q in result if q.difficulty == difficulty]
        return result


@dataclass
class QuizConfig:
    counts_by_difficulty: Dict[str, int] = field(default_factory=dict)
    topic: Optional[str] = None


@dataclass
class QuizQuestion:
    question: Question
    user_answer: Any = None
    is_correct: bool = False


@dataclass
class QuizResult:
    quiz_questions: List[QuizQuestion]
    score: float
    details: List[Dict[str, Any]]


class QuizGenerator:
    def __init__(self, bank: QuestionBank):
        self.bank = bank

    def generate_quiz(self, config: QuizConfig, num_questions: Optional[int] = None) -> List[Question]:
        selection: List[Question] = []
        if config.counts_by_difficulty:
            for diff, count in config.counts_by_difficulty.items():
                pool = self.bank.filter(topic=config.topic, difficulty=diff)
                if not pool:
                    continue
                selection.extend(random.sample(pool, min(count, len(pool))))
        else:
            pool = self.bank.filter(topic=config.topic)
            if num_questions:
                selection = random.sample(pool, min(num_questions, len(pool)))
            else:
                selection = pool
        random.shuffle(selection)
        return selection


class QuizRunner:
    def __init__(self) -> None:
        self.metrics: Dict[int, Dict[str, int]] = {}

    def ask_question(self, q: Question) -> QuizQuestion:
        print(f"\nQuestion ({q.difficulty}, {q.topic}): {q.question}")
        user_answer: Any
        if q.type == "mcq":
            for idx, choice in enumerate(q.choices or []):
                print(f"  {idx + 1}. {choice}")
            user_answer = input("Your choice (number): ").strip()
            try:
                user_idx = int(user_answer) - 1
                is_correct = user_idx == q.correct
                user_answer = user_idx
            except ValueError:
                is_correct = False
        else:
            user_answer = input("Your answer: ").strip().lower()
            is_correct = user_answer == (q.answer or "").lower()

        stats = self.metrics.setdefault(q.id, {"asked": 0, "correct": 0})
        stats["asked"] += 1
        if is_correct:
            stats["correct"] += 1
            print("Correct!")
        else:
            print(f"Incorrect. Explanation: {q.explanation}")
        return QuizQuestion(q, user_answer, is_correct)

    def run(self, questions: List[Question]) -> QuizResult:
        quiz_questions = [self.ask_question(q) for q in questions]
        correct_answers = sum(1 for q in quiz_questions if q.is_correct)
        score = (correct_answers / len(quiz_questions) * 100) if quiz_questions else 0.0
        details = [
            {
                "question": q.question.question,
                "user_answer": q.user_answer,
                "is_correct": q.is_correct,
                "explanation": q.question.explanation,
            }
            for q in quiz_questions
        ]
        return QuizResult(quiz_questions, score, details)


def save_metrics(runner: QuizRunner, path: str = "metrics.pkl") -> None:
    with open(path, "wb") as f:
        pickle.dump(runner.metrics, f)


def load_metrics(path: str = "metrics.pkl") -> Dict[int, Dict[str, int]]:
    with open(path, "rb") as f:
        return pickle.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Practice Test Generator")
    parser.add_argument("--bank", default="questions.json", help="Path to the question bank file.")
    parser.add_argument("--topic", help="Topic to filter questions.")
    parser.add_argument("--num_questions", type=int, help="Number of questions if not specifying difficulties.")
    parser.add_argument("--easy", type=int, default=0)
    parser.add_argument("--medium", type=int, default=0)
    parser.add_argument("--hard", type=int, default=0)
    args = parser.parse_args()

    bank = QuestionBank.from_json(args.bank)
    counts = {
        diff: count
        for diff, count in zip(["easy", "medium", "hard"], [args.easy, args.medium, args.hard])
        if count > 0
    }
    cfg = QuizConfig(topic=args.topic, counts_by_difficulty=counts)
    generator = QuizGenerator(bank)
    questions = generator.generate_quiz(cfg, num_questions=args.num_questions)
    runner = QuizRunner()
    result = runner.run(questions)

    print(f"\nQuiz complete. Score: {result.score:.1f}%")
    print("Details:")
    for d in result.details:
        print("-", d)


if __name__ == "__main__":
    main()
