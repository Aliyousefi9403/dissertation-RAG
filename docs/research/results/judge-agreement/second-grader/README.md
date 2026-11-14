# Second grader

The same 75 answers the first grader scored (`../grading-sheet.csv`), with the grade column empty.
The second grader does not see the first grader's grades, the judge's scores or the conditions.

- `AegisRAG-second-grader-sheet.xlsx`: the sheet to fill in (instructions on the first tab).
- `grading-sheet.csv`: the same rows as CSV, in the layout `judge_agreement.py` reads.

When the filled sheet comes back, its grades go into `grading-sheet.csv` in this folder and
agreement is computed three ways: second grader vs judge, second grader vs first grader, and
judge vs the mean of both graders. The key is `../grading-key.json`.
