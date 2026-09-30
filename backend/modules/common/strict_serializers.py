from collections.abc import Mapping
from typing import Any, cast

from rest_framework import serializers


class StrictSerializer(serializers.Serializer[Any]):
    """Reject unknown input fields instead of silently ignoring attempted overrides."""

    def to_internal_value(self, data: Any) -> dict[str, Any]:
        if isinstance(data, Mapping):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {str(field): ["Unknown field."] for field in sorted(unknown, key=str)}
                )
        return cast(dict[str, Any], super().to_internal_value(data))
