from typing import Annotated
from pydantic.dataclasses import dataclass
from annotated_doc import Doc
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: Annotated[str, Field(min_length=1), Doc("Name of the ingredient")]
    ingredient_type: Annotated[str, Field(min_length=1), Doc("Type of the ingredient, for example 'fruit' or 'condiment'")]
    ingredient_variety: Annotated[str|None, Field(), Doc("If applicable, what variety is this, e.g. for a pear, 'Conference'")]
    quantity: Annotated[str, Field(min_length=1), Doc("Quantity of the ingredient")]