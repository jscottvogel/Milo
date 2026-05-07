def wrap_untrusted(content: str) -> str:
    """
    Implements the <untrusted> content wrapper described in spec Section 5.5.
    Every tool result that contains third-party content is wrapped before being returned to the model.
    """
    return f"<untrusted>\n{content}\n</untrusted>"
