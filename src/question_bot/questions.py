from typing import Dict, List, Optional


class Question:
    def __init__(self, question_page: Dict, concept_id: str):
        assert question_page["object"] == "page"
        self.question_id = (
            f'{concept_id}_{question_page["properties"]["ID"]["title"][0]["text"]["content"]}'
        )
        self.question_type = question_page["properties"]["Question type"]["select"]["name"]
        self.answer_type = question_page["properties"]["Answer type"]["select"]["name"]
        self.correct_answer = question_page["properties"]["Answer"]["rich_text"][0]["text"][
            "content"
        ]
        self.question_text = ""
        self.feedback = ""

    def get_text_from_question_blocks(self, question_block_list: List):
        is_feedback = False
        for question_block in question_block_list:
            if question_block["type"] == "paragraph":
                is_feedback = says_feedback(question_block) or is_feedback
                if not is_feedback:
                    if len(question_block["paragraph"]["text"]) > 0:
                        self.question_text += question_block["paragraph"]["text"][0]["text"][
                            "content"
                        ]
                    self.question_text += "\n"
                # Below skips the word 'feedback'
                elif (
                    len(question_block["paragraph"]["text"]) > 0
                    and question_block["paragraph"]["text"][0]["text"]["content"].lower()
                    != "feedback"
                ):
                    self.feedback += question_block["paragraph"]["text"][0]["text"]["content"]


def says_feedback(block_dict: Dict) -> bool:
    if len(block_dict["paragraph"]["text"]) > 0:
        return block_dict["paragraph"]["text"][0]["text"]["content"].lower() == "feedback"
    else:
        return False
