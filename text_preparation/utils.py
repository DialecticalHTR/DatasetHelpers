def string_index_replace(text: str, index: int, to_insert: str) -> str:
    return text[:index] + to_insert + text[index+1:]
