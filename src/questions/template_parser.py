import json
import random
import re
import warnings
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from questions.utils import SampledParamsDict


class ParsingError(BaseException):
    pass


ParamOptionsDict = Dict[str, List[Any]]


NUMBER_REGEX = r"-?\d+\.?\d*(e-?\d+)?"
STRING_REGEX = """("[^"]*"|'[^']*'|[\u201c\u201d][^\u201c\u201d]*[\u201c\u201d]|[\u2018\u2019][^\u2018\u2019]*[\u2018\u2019])"""
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


def check_valid_params_exist(
    param_options: ParamOptionsDict, params_to_avoid: Optional[List[SampledParamsDict]] = None
) -> bool:
    """Check that at least one valid parameter combination exists."""
    is_valid = params_to_avoid is None or len(params_to_avoid) < np.prod(
        [len(vals) for vals in param_options.values()]
    )
    if not is_valid:
        warnings.warn(
            f"All possible parameter values have been sampled."
            f"\nparam_option_dict: {param_options}\nparams_to_avoid: {params_to_avoid}"
        )
    return is_valid


def sample_params(
    param_options: ParamOptionsDict, params_to_avoid: Optional[List[SampledParamsDict]] = None
) -> Optional[SampledParamsDict]:
    """Samples question template parameter values from possible options from a uniform categorical
    distribution.

    Redraw if the sampled parameters are in the list of params_to_avoid, unless all possible values
    are in that list.
    """
    if not check_valid_params_exist(param_options, params_to_avoid):
        return None
    for _ in range(10000):
        sampled_params = {
            name: str(random.choice(value_options)) for name, value_options in param_options.items()
        }
        if params_to_avoid is None or sampled_params not in params_to_avoid:
            return sampled_params
    raise Exception(
        f"Could not sample parameters from {param_options} after 10000 tries, while avoiding {params_to_avoid}"
    )


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
            raise ParsingError(
                f"Error when parsing:\n\n{text}\nWith params: {sampled_params}\n\n{e}"
            )

    return re.sub(r"(<<([^>]+)>>)", replace_with_expression_output, text)


def convert_string_to_python(value: str) -> str:
    return value if is_number(value) or value.startswith("[") else f'"{value}"'


def run_python_code_string(python_code: str) -> str:
    """Runs Python code in a string and outputs it as a string."""
    try:
        f = StringIO()
        with redirect_stdout(f):
            exec(
                f"A={python_code}\nprint(remove_floating_point_errors(A) if isinstance(A, float) else A)"
            )
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
    for line in template_text.splitlines():
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

    # replace strings starting and ending with ' with double quotes
    values_string = re.sub(STRING_REGEX, lambda x: '"' + x.group(0)[1:-1] + '"', regex.groups()[1])

    # Replace outside { and } with [ and ] to make it valid json
    values_string = "[" + values_string[1:-1] + "]"

    # Prevents a bug due to json.loads() erroring due to latex \ in strings in params
    values_string = re.sub(STRING_REGEX, lambda x: x.group(0).replace("\\", "\\\\"), values_string)

    return regex.groups()[0], json.loads(values_string)


def param_line_regex(line: str) -> Optional[re.Match]:
    """Matches line with regex for parameter line.

    Returns:
        None if not a match, otherwise a re.Match object with .groups() corresponding to contents
         of normal brackets (), ordered by first open bracket (.
    """
    param_element_regex = f"({NUMBER_REGEX}|{STRING_REGEX}|{LIST_REGEX})"
    return re.fullmatch(
        r"\s*param\s+([^-{}:@&%$£?!~#+=,]+):\s*({("
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


def remove_floating_point_errors(num: float) -> float:
    """Remove floating point errors from numbers."""
    return round(num, 4) if round(num, 0) != round(num, 4) else int(round(num, 0))
