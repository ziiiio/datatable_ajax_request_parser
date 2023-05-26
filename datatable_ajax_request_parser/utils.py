def transform_to_bool(bool_value: str | bool) -> bool:
    if type(bool_value) == bool:
        return bool_value

    if not bool_value:
        return False

    if bool_value == 'true':
        return True
    elif bool_value == 'false':
        return False

    raise ValueError(f'Value {bool_value} is not recognised')
