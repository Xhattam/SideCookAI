from typing import Annotated

from pydantic import BaseModel, Field
from annotated_doc import Doc


class Quantity(BaseModel):
    value: Annotated[int|float, Field(min_length=1), Doc("The weight, volume or absolute count for an ingredient")]

