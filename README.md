# Practice Test Generator

A simple command-line utility for generating practice quizzes from a JSON
question bank. Supports multiple choice and short-answer questions, tracks
user metrics, and can filter by topic and difficulty.

## Setup

No external dependencies are required beyond Python 3.7+.

## Usage

1. Prepare a question bank in JSON format (see `questions.json` for an
   example).  Each question can include difficulty, topic, tags, and an
   explanation shown when the answer is incorrect.
2. Run the quiz:

   ```bash
   python quiz.py --bank questions.json --topic geography --easy 10
   ```

   The above command would attempt to generate a quiz with 10 easy geography
   questions.  You can mix difficulty counts (e.g. `--easy 5 --medium 3 --hard 2`)
   or simply request a total number of questions via `--num_questions`.

3. After the quiz completes, the program reports your score and provides
   explanations for missed questions.  Metrics about how often a question is
   asked and answered correctly are stored in memory and can be saved with
   `save_metrics`.

## Saving and Loading Metrics

```python
from quiz import QuizRunner, save_metrics, load_metrics

runner = QuizRunner()
# ... run a quiz ...
save_metrics(runner, "metrics.pkl")
metrics = load_metrics("metrics.pkl")
```

## Importing/Exporting Questions

Questions can be exported back to JSON using `QuestionBank.to_json`.

```python
from quiz import QuestionBank

bank = QuestionBank.from_json("questions.json")
bank.to_json("exported_questions.json")
```

## License

MIT
