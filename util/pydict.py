import json

file_header = """# What's a .pydict?
# It's a python dict literal used to store data instead of json. 
# Why? So we can have multiline blocks with triple quotes.
# It's interpreted with literal_eval, and should be safe from code injection.
# Comments will be stripped on saving (besides this header).

# noinspection PyStatementEffect
"""


def dump_dict(dict_to_dump):
    json_str = json.dumps(dict_to_dump, indent=4, ensure_ascii=False)
    dict_str = file_header
    for line in json_str.split('\n'):  # This loop converts "\n" in json to actual newlines
        if "\\n" not in line:  # literal "\n" not a newline character.
            dict_str += line + '\n'
            continue
        subline_1 = line.split("\\n")[0]
        # might not start with a newline:
        quote_index = subline_1.rindex('"')
        # add two quotes to make it a multiline block
        dict_str += subline_1[:quote_index] + '""' + subline_1[quote_index:] + '\n'
        for subline in line.split("\\n")[1:-1]:
            dict_str += subline + '\n'
        dict_str += line.split("\\n")[
                        -1] + '""' + '\n'  # finish the multiline block, adding two quotes to the existing one
    return dict_str
