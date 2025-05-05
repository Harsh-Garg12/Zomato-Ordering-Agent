from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
from . import llm, OverallState, InputState


guardrails_system = """
As an intelligent assistant, your primary objective is to decision strictly on the following basis:

1. If the question is related to food ordering/listing then output "zomato".

3. If the question is not related to food or restaurant then output "end".
.
To make this decision, assess the content of the question and determine if it refers to any food, food order, detail about food or restaurant or details about restaurant,
or related topics. Provide only the specified output: "zomato" or "end".
"""

guardrails_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            guardrails_system,
        ),
        (
            "human",
            ("{question}"),
        )
    ]
)

class GuardrailsOutput(BaseModel):
  decision: Literal["food", "restaurant", "end"] = Field(
      description="Decision on whether the question is related to foods or restaurant or anything else"
  )

guardrails_chain = guardrails_prompt | llm.with_structured_output(GuardrailsOutput)

def guardrails(state: InputState) -> OverallState:
    """
    Decides if the question is related to foods or restaurant or not.
    """

    guardrails_output = guardrails_chain.invoke({"question": state.get("question")})
    database_records = None

    if guardrails_output.decision == "end":
      database_records = "This questions is not about food (ordering/detail) or their related. Therefore I cannot answer this question."

    return {
        "next_action": guardrails_output.decision,
        "database_records": database_records,
        "steps": ["guardrail"],
    }