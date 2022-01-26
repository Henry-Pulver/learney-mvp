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
What shape matrix results from $$\mathbf{A}\times\mathbf{B}$$?
"""

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
In this case, that means an 4 by 4 matrix.
"""
