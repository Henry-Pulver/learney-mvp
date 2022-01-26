import json
import re
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np

from questions.utils import SampledParamsDict, get_frontend_id


class ParsingError(BaseException):
    pass


ParamOptionsDict = Dict[str, List[Any]]


def question_from_template(
    template_id: UUID, template_text: str, sampled_params: SampledParamsDict
) -> Dict[str, Any]:
    """Gets question dictionary from a template and set of sampled parameters."""
    text_expanded = expand_params_in_text(template_text, sampled_params)
    question_text, answers, feedback, is_feedback = "", {}, "", False
    for index, line in enumerate(text_expanded.splitlines()):
        is_feedback = is_feedback or says_feedback(line)
        if line:
            regex = answer_regex(line)
            if not is_feedback and regex is not None:
                answers[regex.groups()[0]] = regex.groups()[1]
            elif not is_feedback:
                question_text += line + "\n"
            elif not says_feedback(line):  # skip the word 'feedback'
                feedback += line + "\n"
    answers_order_randomised = np.random.shuffle([a for a in answers.keys()])
    return {
        "id": get_frontend_id(template_id, sampled_params),
        "question_text": question_text,
        "answers": answers,
        "answers_order_randomised": answers_order_randomised,
        "feedback": feedback,
        "params": sampled_params,
    }


def get_number_of_answers(template_text: str) -> int:
    return sum(answer_regex(line) is not None for line in template_text.splitlines())


def says_feedback(line: str) -> bool:
    return re.search(r"^\s*[fF]eedback:?\s*$", line) is not None


def answer_regex(line: str) -> Optional[re.Match]:
    return re.search(r"^\s*([abcdABCD])[).]\s*(\S+.*)", line)


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
            python_expression = python_expression.replace(variable, value)
        return run_python_code_string(python_expression)

    return re.sub(r"(<<([^>]+)>>)", replace_with_expression_output, text)


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
    params, _ = parse_params(template_text)
    return int(np.prod([len(values) for values in params.values()]))


def parse_params(template_text: str) -> Tuple[ParamOptionsDict, str]:
    """Parses question template parameters from the full question template.

    Args:
        template_text: question template string

    Returns:
        tuple of [Parameter options, template text with parameter lines removed]
    """
    params = {}
    for count, line in enumerate(template_text.splitlines()):
        if is_param_line(line):
            param_name, possible_values = parse_param_line(line)
            params[param_name] = possible_values
        elif params and line:  # Allows empty lines @ start & between params and question
            template_text = "\n".join(template_text.splitlines()[count:])
            return params, template_text
    raise ParsingError(f"Following question template invalid - missing question!\n{template_text}")


def parse_param_line(line: str) -> Tuple[str, List[Any]]:
    """Parse 1 line from a question template starting with 'param '."""
    regex = param_line_regex(line)
    if regex is None:
        raise ParsingError(f"{line}\n is an invalid question template parameter line")
    values_string = regex.groups()[1].replace("{", "[").replace("}", "]").replace("'", '"')
    return regex.groups()[0], json.loads(values_string)


def param_line_regex(line: str) -> Optional[re.Match]:
    """Matches line with regex for parameter line.

    Returns:
        None if not a match, otherwise a re.Match object with .groups() corresponding to contents
         of normal brackets (), ordered by first open bracket (.
    """
    return re.fullmatch(
        r"^\s*param\s([^-{}:@&%$£?!~#+=,]+):\s({([^-{}:@&%$£?!~#+=,]+,\s*)+[^-{}:@&%$£?!~#+=,]+})\s*$",
        line,
    )


def is_param_line(line: str) -> bool:
    return param_line_regex(line) is not None
