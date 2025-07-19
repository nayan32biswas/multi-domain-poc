from typing import Any

from pydantic import BaseModel
from pydantic.v1.utils import deep_update


def update_partially(target: Any, source: BaseModel, exclude: Any = None) -> Any:
    cls = target.__class__
    update_data = source.model_dump(exclude_unset=True, exclude=exclude)

    target = cls(
        **deep_update(
            target.model_dump(exclude=cls.get_relational_field_info().keys()),
            update_data,
        )
    )

    return target
