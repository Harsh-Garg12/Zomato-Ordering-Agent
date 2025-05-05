from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Union, Optional
from .. import llm, embedding_model
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import os
import json

CURRENT_DIR = os.path.dirname(__file__)
file_path = os.path.join(CURRENT_DIR, 'examples_for_entity_extraction.json')

with open(file_path, 'r') as f:
    examples_for_entity_extraction = json.load(f)

documents = [
    Document(page_content=ex["question"], metadata={"order_info": ex["order_info"]})
    for ex in examples_for_entity_extraction
]

vectorstore = FAISS.from_documents(
    documents=documents,
    embedding=embedding_model
)

entity_example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples=examples_for_entity_extraction,
    embeddings = embedding_model,
    vectorstore_cls=vectorstore,
    k=5,
    input_keys=["question"],
)

class RestaurantNamePair(BaseModel):
  restaurant_name: str
  condition: bool

class OrderFiltering(BaseModel):
  food_rating_filter: Optional[Literal["ASC", "DESC"]]=None
  food_price_filter: Optional[Literal["ASC", "DESC"]]=None
  restaurant_rating_filter: Optional[Literal["ASC", "DESC"]]=None

# Extract entities from text
class EntityInfoItem(BaseModel):
    """Identifying information about entities."""
    food_name: str = Field(
        description="""
        It represents the food (dish) name only, if no name is mentioned consider the default value only.

        IMPORTANT: It's not a common noun remember that, words like "food", "dish" or their synonyms are not valid values.

        For example:
        question: "Hey, what's the worst rated dish you have?"
        food_name: ""

        question: "Hey, I want to eat some spicy food?"
        food_name: ""

        question: "Are they any option for mango shakes?"
        food_name: "shakes"

        question: "Hello, I'm looking for a meal of pizza."
        food_name: "pizza"
        """,
        default=""
    )

    flavour: str = Field(
        description="""
        It represents the flavour of the food(dish) described in the question.
        """,
        default=""
    )
    bestseller: Literal["true", "false"] = Field(
        ...,
        description="""
        Whether the food is supposed to be a bestseller or not, it's value is "true" only when the keyword like bestseller, best selling item, popular, recommended, is present.
        """,
    )

    type_: Literal["veg", "non-veg", "egg", "not_mentioned"] = Field(
        description="""
        If the food type is mentioned from any one of the following types: veg, non-veg or egg. If nothing is present about the food type then consider its value equal to "not_mentioned".
        Never consider any other value for the food type. Only permissible values are "veg", "non_veg", "egg" and "not_mentioned".
        """,
        default="not_mentioned"
    )

    food_rating: Union[float, Literal["not_available"]] = Field(
        ...,
        description="""
        Represents the food_rating of the food. Unless any "numeric value" is present then rating is equal to "not_available".
        """,
    )

    food_price: float = Field(
        description="""
        Represents the price of the food.
        """,
        default=0.0
    )

    quantity: int = Field(
        description="""
        It represents the quantity of food mentiioned in the question, if nothing is mentioned consider the default value.

        For example: if question is "Hey, I want to order 2 scoops of ice cream" then quantity is equal to 2.

        """,
        default = 1
    )

    restaurant_name_pair: List[RestaurantNamePair] = Field(
        description="""
        A list of (restaurant_name, condition) pairs where:
        - `restaurant_name` is a string representing the name.
        - `condition` is a boolean: True means the name should be matched using CONTAINS,
          False means the name should NOT be matched using CONTAINS.

        Example: [("restaurant_name": "KFC", "condition": True), ("restaurant_name": "McDonald", "condition": False)]

        VERY IMPORTANT: Don't change anything with characters of the name, keep each character
        same as it is, even the apostrophe character, comma, quotes, etc.
        """,
        default=[]
    )


    restaurant_deliverables: str = Field(
        description="""
        It represent the kind of food is expected from the restaurant like dessert, sweet, north india, south indian, italian food, turkish, spanish food, chinese food, juices, shakes, mountain food, drinks etc.
        If nothing is expected from the restaurant then consider the default value.
        """,
        default=""
    )

    restaurant_rating: Union[float, Literal["not_available"]] = Field(
        ...,
        description="""
        Represents the delivery_rating of the restaurant. Unless any "numeric value" is present then rating is equal to "not_available".
        """,
    )

    restaurant_phone_number: str = Field(
        description="""
        Represent the phone_number of a restaurant if the input question contains it.
        """,
        default=""
    )

    restaurant_address: str = Field(
        description="""
        Represent the address of a restaurant if the input question contains it.
        """,
        default = ""
    )

    limit: int = Field(
        description="""
        It represent the number of records user demanded in the question.

        Examples: 
        1. question: "Hey, show me the most expensive dish", limit: 1
        2. question: "Show me the top 10 cheapest food option", limit: 10
        3. question: "show me the cheapest option for pizza at zomato.", limit: 1

        IMPORTANT: Unless keywords like most expensive/cheapest, top 5 or top n (n could be any integer), most pricest, etc are present consider the default value 0 only.
        """,
        default=0
    )

    order_filter: Optional[OrderFiltering] = Field(
        description="""
        It represents the way/order in which user wants his/her records to be arranged based on the context of user question.

        Examples:
        1. question: "Hey, show me the most expensive dish", order_filter: {"food_price_filter": "DESC"}
        2. question: "Show me the top 10 cheapest food option from high rating restaurants", order_filter: {"restaurant_rating_filter": "DESC", "food_price_filter": "ASC"}
        3. question: "show me an option for kadai paneer with good rating", order_filter: {"food_rating_filter": "DESC"}

        IMPORTANT: This is an optional field consider it only when it is reflected from the user question that the user wants his/her records to arranged in a specific way.
        """
    )

    @field_validator("food_rating", "restaurant_rating", mode="before")
    @classmethod
    def parse_rating(cls, value):
        try:
            return str(float(value))
        except (ValueError, TypeError):
            return "not_available"

    @field_validator('restaurant_name_pair')
    @classmethod
    def validate_pairs(cls, v):
        if not all(isinstance(item, RestaurantNamePair) for item in v):
            raise ValueError("Each item in restaurant_name_pair must be a RestaurantNamePair object")
        return v

class Entities(BaseModel):
  order_info: List[EntityInfoItem] = Field(
        default = [],
        description="""
        It represents the list of dictionaries of type FoodInfoItem. The number of dictionaries in the list is always equal to the number of food(dish) names present in the question.
        """
  )

entity_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You're an intelligent assistant who is expert in understanding the requirement of the user only related to food ordering.
            """
        ),
        (
            "human",
            """
            Use the given format to extract information from the following, strictly be consistent with your response don't change it for the same question."

            "input: {question}",

            Below are a list of examples for a reference.
            {examples}
            """
        ),
    ]
)

entity_chain = entity_prompt | llm.with_structured_output(Entities)

async def get_entities(question):
    NL = '\n'
    fewshot_examples = (NL*2).join(
        [
            f"Question: {el['question']}{NL}OrderInfo:{el['order_info']}"
            for el in entity_example_selector.select_examples(
                {"question": question}
            )
        ]
    )

    extracted_entities = await entity_chain.ainvoke({"question": question, "examples": fewshot_examples})
    return extracted_entities