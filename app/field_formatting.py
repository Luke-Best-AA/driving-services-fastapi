def dates_to_string(policy):
    if not isinstance(policy["start_date"], str):
        policy["start_date"] = policy["start_date"].strftime("%Y-%m-%d")
    if not isinstance(policy["end_date"], str):
        policy["end_date"] = policy["end_date"].strftime("%Y-%m-%d")

def capitalise_first(s):
    return s[:1].upper() + s[1:] if s else s