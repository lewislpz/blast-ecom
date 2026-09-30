from __future__ import annotations

from typing import Any

from rest_framework import serializers


class ProblemFieldErrorSerializer(serializers.Serializer[Any]):
    field = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()


class ProblemDetailSerializer(serializers.Serializer[Any]):
    type = serializers.URLField()
    title = serializers.CharField()
    status = serializers.IntegerField()
    detail = serializers.CharField()
    code = serializers.CharField()
    request_id = serializers.UUIDField()
    field_errors = ProblemFieldErrorSerializer(many=True, required=False)
