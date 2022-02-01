import json
import re
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from questions.utils import SampledParamsDict


class ParsingError(BaseException):
    pass


ParamOptionsDict = Dict[str, List[Any]]


NUMBER_REGEX = r"-?\d+\.?\d*(e-?\d+)?"
STRING_REGEX = r"""("[^"]+"|'[^']+')"""
LIST_REGEX = f"\[(({NUMBER_REGEX}|{STRING_REGEX})+.*,\s*)*({NUMBER_REGEX}|{STRING_REGEX})]"


def is_number(value: str) -> bool:
    return re.fullmatch(NUMBER_REGEX, value) is not None


def is_string(value: str) -> bool:
    return re.fullmatch(STRING_REGEX, value) is not None


def is_list(value: str) -> bool:
    return re.fullmatch(LIST_REGEX, value) is not None


def says_feedback(line: str) -> bool:
    return re.search(r"^\s*[fF]eedback:?\s*$", line) is not None


def answer_regex(line: str) -> Optional[re.Match]:
    return re.search(r"^\s*\(?([abcdABCD])[).]\s*(\S+.*)", line)


def sample_params(param_option_dict: ParamOptionsDict) -> SampledParamsDict:
    """Samples question template parameter values from possible options from a uniform categorical
    distribution."""
    return {
        name: str(np.random.choice(param_options))
        for name, param_options in param_option_dict.items()
    }


def expand_params_in_text(text: str, sampled_params: SampledParamsDict) -> str:
    """
    Expand expressions in the text - replace occurrences of <<>> with the output
     of the python expressions contained within them.
    """

    def replace_with_expression_output(match: re.Match) -> str:
        python_expression = match.groups()[1]
        for variable, value in sampled_params.items():
            python_expression = python_expression.replace(variable, convert_string_to_python(value))
        try:
            return run_python_code_string(python_expression)
        except ParsingError as e:
            raise ParsingError(f"Error when parsing: {text}\nWith params: {sampled_params}\n{e}")

    return re.sub(r"(<<([^>]+)>>)", replace_with_expression_output, text)


def convert_string_to_python(value: str) -> str:
    return value if is_number(value) or value.startswith("[") else f'"{value}"'


def run_python_code_string(python_code: str) -> str:
    """Runs Python code in a string and outputs it as a string."""
    try:
        f = StringIO()
        with redirect_stdout(f):
            exec(f"print({python_code})")
        return f.getvalue()[:-1]  # print() automatically adds a \n at the end - cut this
    except Exception as e:
        raise ParsingError(f"Python inside <<>> is invalid!\n Code: {python_code}\nError: {e}")


def number_of_questions(template_text: str) -> int:
    """Get the number of questions that can be generated from a template from a parameter options
    dictionary."""
    params = parse_params(template_text)
    return int(np.prod([len(values) for values in params.values()]))


def parse_params(template_text: str) -> ParamOptionsDict:
    """Parses question template parameters from the full question template.

    Args:
        template_text: question template string

    Returns:
        Parameter options dictionary, {param_name: [list of possible values]}
    """
    params = {}
    for count, line in enumerate(template_text.splitlines()):
        if is_param_line(line):
            param_name, possible_values = parse_param_line(line)
            params[param_name] = possible_values
        elif contains_non_whitespace_characters(line):
            # If not empty & not a parameter line, must be question text
            return params
    raise ParsingError(f"Following question template invalid - missing question!\n{template_text}")


def parse_param_line(line: str) -> Tuple[str, List[Any]]:
    """Parse 1 line from a question template starting with 'param '."""
    regex = param_line_regex(line)
    if regex is None:
        raise ParsingError(f"{line}\n is an invalid question template parameter line")
    # \u201c and \u201d are the unicode characters that " is turned into on Notion
    values_string = (
        re.sub(r"""(['\u201c\u201d])""", lambda x: '"', regex.groups()[1])
        .replace("{", "[")
        .replace("}", "]")
    )
    return regex.groups()[0], json.loads(values_string)


def param_line_regex(line: str) -> Optional[re.Match]:
    """Matches line with regex for parameter line.

    Returns:
        None if not a match, otherwise a re.Match object with .groups() corresponding to contents
         of normal brackets (), ordered by first open bracket (.
    """
    param_element_regex = f"({NUMBER_REGEX}|{STRING_REGEX}|{LIST_REGEX})"
    return re.fullmatch(
        r"\s*param\s([^-{}:@&%$£?!~#+=,]+):\s({("
        + param_element_regex
        + ",\s*)*"
        + param_element_regex
        + "})\s*",
        line,
    )


def is_param_line(line: str) -> bool:
    return param_line_regex(line) is not None


def contains_non_whitespace_characters(line: str) -> str:
    return line if re.match(r"\S+", line) is not None else ""


def remove_start_and_end_newlines(text: str) -> str:
    """Remove line-breaks ('\n') at the start & end of the string."""
    while text.startswith("\n"):
        text = text[1:]
    while text.endswith("\n"):
        text = text[:-1]
    return text
