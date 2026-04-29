from src.deterministic_rails import detectar_toxicidade, detectar_out_of_scope

def check_input(context=None):
    text = ""
    if context and "user_message" in context:
        text = context["user_message"]

    tox = detectar_toxicidade(text)
    if not tox.allowed:
        return False

    return True

def check_output(context=None):
    return True
