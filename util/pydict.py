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
        # might not start with a newline:
        dict_str += quote_to_block_quote(line.split("\\n")[0])
        for subline in line.split("\\n")[1:-1]:
            dict_str += subline + '\n'
        dict_str += quote_to_block_quote(line.split("\\n")[-1])
    return dict_str


def quote_to_block_quote(line):
    quote_index = line.rindex('"')
    # add two quotes to make it a multiline block
    return line[:quote_index] + '""' + line[quote_index:] + '\n'
