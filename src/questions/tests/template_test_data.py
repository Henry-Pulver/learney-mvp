from typing import Dict


class QuestionWithParamsOne:
    QUESTION_TEMPLATE_STRING = r"""param A: {1, 2, 3, 4, 5, 6, 7, 8, 9}

param B: {1, 2, 3, 4, 5, 6, 7, 8, 9}

$$\mathbf{A}$$ is a $$<<A>> \times <<B>>$$ matrix, and $$\mathbf{B}$$ is a $$<<B>> \times <<A>>$$ matrix.
What shape matrix results from $$\mathbf{A}\times\mathbf{B}$$?

a) $$<<B>> \times <<B>>$$
b) $$<<A>> \times <<A>>$$
c) $$<<A>> \times <<B>>$$
d) $$<<A * A>> \times <<B * B>>$$

Feedback
In matrix multiplication, the order of operation matters (i.e. A x B ≠ B x A).
We take the rows of the first matrix, and multiply them by the columns of the second.
In practice, this means the size of the output matrix will be $$n(rows(A)) \times n(columns(B))$$
In this case, that means an <<A>> by <<A>> matrix."""

    PARAMS_DICT = {"A": "4", "B": "7"}

    QUESTION_TEXT = r"""$$\mathbf{A}$$ is a $$4 \times 7$$ matrix, and $$\mathbf{B}$$ is a $$7 \times 4$$ matrix.
What shape matrix results from $$\mathbf{A}\times\mathbf{B}$$?"""

    CORRECT_ANSWER_LETTER = "a"
    CORRECT_ANSWER = r"$$7 \times 7$$"

    ANSWERS = [
        r"$$7 \times 7$$",
        r"$$4 \times 4$$",
        r"$$4 \times 7$$",
        r"$$16 \times 49$$",
    ]

    FEEDBACK = r"""In matrix multiplication, the order of operation matters (i.e. A x B ≠ B x A).
We take the rows of the first matrix, and multiply them by the columns of the second.
In practice, this means the size of the output matrix will be $$n(rows(A)) \times n(columns(B))$$
In this case, that means an 4 by 4 matrix."""


class QuestionWithParamsTwo:
    QUESTION_TEMPLATE_STRING = r"""param A: {-5, -3, -1, 1, 3, 5}
param B: {-4, -2, 0, 2, 4, 6}
param C: {5, 8, 10, -2, -4, -6}
param D: {7, 9, 11, -3, -5, -7}
Which of the following is a symmetric matrix?
(a) $$\begin{bmatrix}    <<A>> & <<B>>\\
    <<-B>> & <<A>>
\end{bmatrix}$$
(b) $$\begin{bmatrix}    <<C>> & <<A>>\\
    <<B>> & <<D>>
\end{bmatrix}$$
(c) $$\begin{bmatrix}    <<C>> & <<A>>\\
    <<A>> & <<D>>
\end{bmatrix}$$
(d) $$\begin{bmatrix}    <<B>> & <<A>>\\
    <<D>> & <<C>>
\end{bmatrix}$$
Feedback
By definition of symmetric matrix $$A^T=A.$$
$$\begin{bmatrix}    <<C>> & <<A>>\\
    <<A>> & <<D>>
\end{bmatrix}^T=\begin{bmatrix}    <<C>> & <<A>>\\
<<A>> & <<D>>
\end{bmatrix}.$$"""
    PARAMS_DICT = {"A": "1", "B": "2", "C": "5", "D": "7"}

    QUESTION_TEXT = r"""Which of the following is a symmetric matrix?"""

    CORRECT_ANSWER_LETTER = "a"
    CORRECT_ANSWER = r"""$$\begin{bmatrix}    1 & 2\\    -2 & 1\end{bmatrix}$$"""

    ANSWERS = [
        r"""$$\begin{bmatrix}    1 & 2\\    -2 & 1\end{bmatrix}$$""",
        r"""$$\begin{bmatrix}    5 & 1\\    2 & 7\end{bmatrix}$$""",
        r"""$$\begin{bmatrix}    5 & 1\\    1 & 7\end{bmatrix}$$""",
        r"""$$\begin{bmatrix}    2 & 1\\    7 & 5\end{bmatrix}$$""",
    ]

    FEEDBACK = r"""By definition of symmetric matrix $$A^T=A.$$
$$\begin{bmatrix}    5 & 1\\
    1 & 7
\end{bmatrix}^T=\begin{bmatrix}    5 & 1\\
1 & 7
\end{bmatrix}.$$"""


class QuestionWithoutParams:
    QUESTION_TEMPLATE_STRING = """Which of the following describes what a matrix is?

a) Rows of symbols of different lengths, addressable by keys

b) A list of numbers arranged in ascending order

c) A rectangular array of numbers, symbols, or expressions

d) Many numbers placed in series

Feedback

A matrix is a rectangular array of numbers, symbols or expressions."""

    PARAMS_DICT: Dict[str, str] = {}

    QUESTION_TEXT = r"""Which of the following describes what a matrix is?"""

    CORRECT_ANSWER_LETTER = "c"
    CORRECT_ANSWER = r"A rectangular array of numbers, symbols, or expressions"

    ANSWERS = [
        "Rows of symbols of different lengths, addressable by keys",
        "A list of numbers arranged in ascending order",
        "A rectangular array of numbers, symbols, or expressions",
        "Many numbers placed in series",
    ]

    FEEDBACK = r"""A matrix is a rectangular array of numbers, symbols or expressions."""
