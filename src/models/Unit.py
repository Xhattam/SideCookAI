from typing import Annotated

from pydantic import BaseModel, Field


class Unit(BaseModel):
    nature: Annotated[str, Field(min_length=1)]