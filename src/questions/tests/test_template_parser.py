from typing import Callable
from uuid import uuid4

import pytest

from questions.template_parser import *

from .template_test_data import *

INVALID_PARAM_LINES = [
    "",
    " ",
    "param ",
    "param A",
    "param A: ",
    "param A: {}",
    "param A {1, 2}",
    "param A: {1}",
    "param : {1, 2}",
    "param A?: {1, 2}",
    "param A: {1, 2",
    "param A: {1, 2,}",
    "param A: {1, 2};",
    "param A: {1, 2} d",
    "param A: {1, 2}}",
    "'param A: {1, 2}'",
    "param A: {1-2, 3}",
]

VALID_PARAM_LINES = [
    ("param A: {1, 2}", "A", [1, 2]),
    ("param Abbbbb: {1, 2}", "Abbbbb", [1, 2]),
    ("param B: {[1], [2]}", "B", [[1], [2]]),
    ("param C: {'1', '2'}", "C", ["1", "2"]),
]


@pytest.mark.parametrize("line", INVALID_PARAM_LINES)
def test_is_param_line__error(line: str) -> None:
    assert not is_param_line(line)


@pytest.mark.parametrize("line", [p[0] for p in VALID_PARAM_LINES])
def test_is_param_line__success(line: str) -> None:
    assert is_param_line(line)


@pytest.mark.parametrize("line", INVALID_PARAM_LINES)
def test_parse_param_line__error(line: str) -> None:
    with pytest.raises(ParsingError):
        parse_param_line(line)


@pytest.mark.parametrize("param_info", VALID_PARAM_LINES)
def test_parse_param_line__success(param_info: Tuple[str, str, List[Any]]) -> None:
    param_name, param_options = parse_param_line(param_info[0])
    assert param_name == param_info[1]
    assert param_options == param_info[2]


@pytest.mark.parametrize("remaining_text", ["Question", "sefoiuahsekf ywesfkjblb"])
@pytest.mark.parametrize(
    "params_info",
    [VALID_PARAM_LINES]
    + [VALID_PARAM_LINES[n + 1 :] + VALID_PARAM_LINES[:n] for n in range(len(VALID_PARAM_LINES))],
)
def test_parse_params__success(
    remaining_text: str, params_info: List[Tuple[str, str, List[Any]]]
) -> None:
    text_to_parse = "".join(line + "\n" for line, _, _ in params_info) + "\n" + remaining_text
    expected_all_param_options = {name: value for _, name, value in params_info}
    all_param_options, text_without_params = parse_params(text_to_parse)
    assert all_param_options == expected_all_param_options
    assert text_without_params == remaining_text


def test_parse_params__error() -> None:
    """Check that it errors when there is no question after the param declarations."""
    text_to_parse = "".join(line + "\n" for line, _, _ in VALID_PARAM_LINES)
    with pytest.raises(ParsingError):
        parse_params(text_to_parse)


@pytest.mark.parametrize(
    "success_test_data",
    [
        ("2 + 2", "4"),
        ("2 * 7", "14"),
        ("3 ** 2", "9"),
        ("1.2 * 5", "6.0"),
        ("1 / 5", "0.2"),
        ("5 % 2", "1"),
        ('"string"', "string"),
        ('"string" + " another_string"', "string another_string"),
        ("[1, 2, 3, 4][3]", "4"),
        ("[1, 2, 3] + [5, 6]", "[1, 2, 3, 5, 6]"),
    ],
)
def test_run_python_code_string__success(success_test_data: Tuple[str, str]) -> None:
    assert success_test_data[1] == run_python_code_string(success_test_data[0])


@pytest.mark.parametrize(
    "failure_test_data",
    [
        "<<2>> + 2",
        r"2 \times 7",
        "3^{2}",
        r"1.2 \times 5",
        r"\frac{1}{5}",
        "5 2",
        '"string',
        '"string" + " another_string',
        "[1, 2, 3, 4][[3]]",
        "[1, 2, 3] * [5, 6]",
    ],
)
def test_run_python_code_string__error(failure_test_data: str) -> None:
    with pytest.raises(ParsingError):
        run_python_code_string(failure_test_data)


@pytest.mark.parametrize(
    "test_data_pairs",
    [
        (r"What is $$2 \times <<A / B>>$$?", lambda a, b: rf"What is $$2 \times {a / b}$$?"),
        (r"What is $$2 \times <<A * B>>$$?", lambda a, b: rf"What is $$2 \times {a * b}$$?"),
    ],
)
@pytest.mark.parametrize("params", [("1", "7"), ("66", "23"), ("4.7", "12")])
def test_expand_params_in_text__success_tricky_numbers(
    test_data_pairs: Tuple[str, Callable], params: Tuple[str, str]
) -> None:
    converted_params = (float(param) if "." in param else int(param) for param in params)
    assert expand_params_in_text(
        test_data_pairs[0], {"A": params[0], "B": params[1]}
    ) == test_data_pairs[1](*converted_params)


@pytest.mark.parametrize(
    "params",
    [
        {"A": [1, 2, 3, 4, 5]},
        {"Beefy": [1, 2, 3, 4, 5]},
        {"A": [[1, 2], [3, 4, 5]]},
        {"A": ["1, 2", "3, 4", "5 n"]},
    ],
)
def test_sample_params(params: ParamOptionsDict):
    for name, v in sample_params(params).items():
        transformed_v = int(v) if v.isnumeric() else json.loads(v) if v.startswith("[") else v
        assert transformed_v in params[name]


@pytest.mark.parametrize(
    "text",
    [
        "<<A>>",
        "<<B>>",
        "<<alpha>>",
        "<<beta>>",
        r"What is $$2 \times <<A>> / <<B>>$$?",
        r"What is $$2 \times <<alpha>> / <<beta>>$$?",
    ],
)
@pytest.mark.parametrize("chosen_params", [("2", "2")])
def test_expand_params_in_text__success_simple(text: str, chosen_params: Tuple[str, str]) -> None:
    ab = "A" in text or "B" in text
    a = "A" if ab else "alpha"
    b = "B" if ab else "beta"
    expected_output = text.replace(f"<<{a}>>", chosen_params[0]).replace(
        f"<<{b}>>", chosen_params[1]
    )
    assert (
        expand_params_in_text(text, {a: chosen_params[0], b: chosen_params[1]}) == expected_output
    )


@pytest.mark.parametrize(
    "data",
    [
        ("", False),
        ("fedback", False),
        ("feeback:", False),
        ("Feedback isn't provided here. This is part of the question.", False),
        ("feedback", True),
        ("Feedback", True),
        (" feedback:", True),
        (" Feedback: ", True),
    ],
)
def test_says_feedback(data: Tuple[str, bool]) -> None:
    assert says_feedback(data[0]) == data[1]


@pytest.mark.parametrize(
    "data",
    [
        ("", False),
        ("a)", False),
        ("a) ", False),
        ("e) There can't be 5 answers!", False),
        ("This isn't an answer. This is part of the question.", False),
        ("a) 7", True),
        ("B) r", True),
        ("c) BOOM", True),
        ("  d) This works", True),
        ("D. So does this", True),
    ],
)
def test_answer_regex(data: Tuple[str, bool]) -> None:
    assert (answer_regex(data[0]) is not None) is data[1]


def test_question_from_template():
    template_id = uuid4()
    _, remaining_text = parse_params(QUESTION_TEMPLATE_STRING)
    question_dict = question_from_template(
        template_id=template_id,
        template_text=remaining_text,
        sampled_params=PARAMS_DICT,
    )
    expected_question_dict = {
        "id": get_frontend_id(template_id, PARAMS_DICT),
        "question_text": QUESTION_TEXT,
        "answers": ANSWERS,
        "feedback": FEEDBACK,
        "params": PARAMS_DICT,
    }
    assert all(
        q_letter in question_dict.pop("answers_order_randomised")
        for q_letter in ["a", "b", "c", "d"]
    )
    assert question_dict == expected_question_dict
