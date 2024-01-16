import json

file_header = """# What's a .pydict?
# It's a python dict literal used to store data instead of json. 
# Why? So we can have multiline blocks with triple quotes.
# It's interpreted with literal_eval, and should be safe from code injection.
# Comments will be stripped on saving (besides this header).

# Supported change modes are "Add", "Replace", or "AddBullet". Use "NoOp" to prevent that entry from being processed.

# noinspection PyStatementEffect
"""

def get_associated_nodes(change):
    expected_ids = []
    if hasattr(change, 'associated_nodes'):
        expected_ids = change['associated_nodes']
    return expected_ids

def dump_dict(dict_to_dump):
    json_str = json.dumps(dict_to_dump, indent=4, ensure_ascii=False)
    dict_str = file_header
    for line in json_str.split('\n'):  # This loop converts "\n" in json to actual newlines
        if "\\n" not in line:  # literal "\n" not a newline character.
            dict_str += line + '\n'
            continue
        # Begin the block quote
        dict_str += quote_to_block_quote(line.split("\\n")[0])
        for sub_line in line.split("\\n")[1:-1]:
            dict_str += sub_line + '\n'
        dict_str += quote_to_block_quote(line.split("\\n")[-1])
    return dict_str


def quote_to_block_quote(line):
    quote_index = line.rindex('"')  # This might not work with escaped quote characters, need to look out for that.
    # add two quotes to make it a multiline block
    return line[:quote_index] + '""' + line[quote_index:] + '\n'
