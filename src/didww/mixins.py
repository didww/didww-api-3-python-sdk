"""Reusable mixins shared across resource hierarchies."""


class RedactsSensitiveAttributes:
    """Provides a `__repr__` that masks values of attribute keys listed in
    ``_sensitive_attrs`` so credentials never leak through default
    ``print()`` / logging / unhandled exception output.

    The wire payload is unaffected — the host class's serializer (e.g.
    ``to_jsonapi``) still emits the real values.

    Used by ``TrunkConfiguration`` and ``AuthenticationMethod``, which
    both expose an ``_attributes`` dict and a ``_sensitive_attrs``
    frozenset that subclasses extend.
    """

    _sensitive_attrs = frozenset()

    def __repr__(self):
        parts = []
        for key, value in self._attributes.items():
            if key in self._sensitive_attrs and value is not None:
                value = "[FILTERED]"
            parts.append(f"{key}={value!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"
