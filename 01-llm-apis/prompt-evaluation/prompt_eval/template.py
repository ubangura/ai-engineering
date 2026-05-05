import re


def escape_newlines(text: str) -> str:
    """Replace literal newlines with the two-character sequence `\\n` so the string is safe to embed on a single line."""
    return text.replace("\n", "\\n")


def render(template_string: str, variables: dict) -> str:
    """Substitute `{name}` placeholders with values from `variables`. `{{` and `}}` are literal braces in the output."""
    for placeholder in re.findall(r"{([^{}]+)}", template_string):
        if placeholder in variables:
            template_string = template_string.replace(
                "{" + placeholder + "}", str(variables[placeholder])
            )
    return template_string.replace("{{", "{").replace("}}", "}")
