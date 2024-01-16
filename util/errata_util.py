from util.log_util import print_styled, STYLES, get_diff, style_text
from util.node_util import get_description, update_page_and_pub
from util.system_util import find_similar_items, get_node_from_system, remove_node
from util.system_globals import rules_list
from util.text_utils import get_bullet_type, column_text_to_paragraph_text


def handle_node_change(old_ids, new_ids):
    # Check if an existing ID is not found / created.
    for old_id in old_ids:
        if old_id not in new_ids:
            print(
                style_text("There is an old instance of this node that needs to be deleted",
                           [STYLES.BOLD, STYLES.RED]))
            remove_node(old_id)


def handle_special_rules_errata(change, mode, page, pub):
    # As of now this assumes format=block
    target = change['target_name']
    print(f"Errata for {target}")
    text_block = change['text']
    new_text = column_text_to_paragraph_text(text_block)
    new_text = new_text.strip().strip('"').strip('”').strip('“')  # Remove any left-in quote characters
    target_paragraph = None
    if 'paragraph' in change.keys():
        target_paragraph = change['paragraph']
    target_sentence = None
    if 'sentence' in change.keys():
        target_sentence = change['sentence']
        if target_paragraph is None:
            target_paragraph = 1  # Assume 1st paragraph
    target_sentence = None
    target_bullet = None
    if 'bullet' in change.keys():
        target_bullet = change['bullet']
    node_to_errata = None
    if target in rules_list.keys():
        print(f"\tRule exists in data files: {rules_list[target]}")
        node_to_errata = get_node_from_system(rules_list[target])
    if node_to_errata is None:
        print("Could not find node for " + target)
        options = find_similar_items(rules_list.keys(), target, similarity_threshold=1)
        print("Did you mean? " + " or ".join(options.keys()))
        exit()
    description = get_description(node_to_errata)
    existing_text = description.text
    # Check existing text isn't already in statement
    check_text = new_text
    if mode == "AddBullet" or (target_bullet and mode == "Replace"):
        check_text = new_text[2:]  # Remove the bullet as the format may have changed
    if check_text in existing_text:
        print("\tErrata appears already applied.")

    else:
        final_text = ""
        if target_sentence and mode == "Replace":
            final_text = replace_sentence_of_paragraph(existing_text, new_text, target_paragraph,
                                                       target_sentence)
        elif mode == "AddBullet":
            final_text = add_new_bullet_to_end(existing_text, new_text)
        elif target_bullet and mode == "Replace":
            final_text = replace_bullet(existing_text, new_text, target_bullet)
        elif target_bullet and mode == "Add":
            final_text = add_to_bullet(existing_text, new_text, target_bullet)
        elif target_paragraph and mode == "Replace":
            final_text = replace_paragraph(existing_text, new_text, target_paragraph)
        elif target_paragraph and mode == "Add":
            final_text = add_to_paragraph(existing_text, new_text, target_paragraph)
        if final_text:
            # Strip whitespace just in case the function left some on at the end
            description.text = final_text.strip()

            # Print that we made a change
            print_styled("\tApplied change", STYLES.PURPLE)
            diff = get_diff(existing_text, description.text, 2)
            print(diff)
    # Update the node's source
    update_page_and_pub(node_to_errata, page, pub)

    # Update list of associated nodes
    change['associated_nodes'] = [rules_list[target]]
    return change['associated_nodes']


def add_to_paragraph(existing_text, new_text, target_paragraph_index):
    print_styled("UNTESTED", STYLES.RED)

    update_success = False
    i = 1
    paragraphs = []
    for paragraph in existing_text.split("\n"):
        if i == target_paragraph_index:
            update_success = True
            paragraphs.append(paragraph + " " + new_text)
        else:
            paragraphs.append(paragraph)
        i += 1
    if update_success:
        return "\n".join(paragraphs)
    return ""


def replace_paragraph(existing_text, new_text, target_paragraph_index):
    print_styled("UNTESTED", STYLES.RED)

    update_success = False
    i = 1
    paragraphs = []
    for paragraph in existing_text.split("\n"):
        if i == target_paragraph_index:
            update_success = True
            paragraphs.append(new_text)
        else:
            paragraphs.append(paragraph)
        i += 1
    if update_success:
        return "\n".join(paragraphs)
    return ""


def replace_sentence_of_paragraph(existing_text, new_text, target_paragraph_index, target_sentence_index):
    print_styled("UNTESTED", STYLES.RED)

    update_success = False
    i = 1
    paragraphs = []
    for paragraph in existing_text.split("\n"):
        if i == target_paragraph_index:
            new_paragraph = replace_sentence(paragraph, new_text, target_sentence_index)
            if new_paragraph != "":
                update_success = True
                paragraphs.append(new_paragraph)
            else:
                paragraphs.append(paragraph)
        else:
            paragraphs.append(paragraph)
        i += 1
    if update_success:
        return "\n".join(paragraphs)
    return ""


def replace_sentence(existing_text, new_text, target_sentence_index):
    print_styled("UNTESTED", STYLES.RED)

    update_success = False
    i = 1
    sentences = []
    for sentence in existing_text.split("."):
        sentence = sentence.strip()
        if i == target_sentence_index:
            update_success = True
            sentences.append(new_text)
        else:
            sentences.append(sentence)
        i += 1
    if update_success:
        return ". ".join(sentences)
    return ""


def replace_bullet(existing_text, new_text, bullet_index):
    print_styled("UNTESTED", STYLES.RED)
    update_success = False

    bullet_type = get_bullet_type(existing_text)

    # Replace whatever the existing bullet was with the matching bullet type
    new_bullet = bullet_type + new_text[1:]

    paragraphs = []
    i = 0
    for line in existing_text.split("\n"):
        if line.startswith(bullet_type):
            i += 1
            if i == bullet_index:
                update_success = True
                paragraphs.append(new_bullet)
                continue
        paragraphs.append(line)
    if update_success:
        return "\n".join(paragraphs)
    return ""


def add_to_bullet(existing_text, new_text, bullet_index):
    print_styled("UNTESTED", STYLES.RED)

    update_success = False

    bullet_type = get_bullet_type(existing_text)

    # Replace whatever the existing bullet was with the matching bullet type
    paragraphs = []
    i = 0
    for line in existing_text.split("\n"):
        if line.startswith(bullet_type):
            i += 1
            if i == bullet_index:
                update_success = True
                paragraphs.append(line + " " + new_text)
                continue
        paragraphs.append(line)
    if update_success:
        return "\n".join(paragraphs)
    return ""


def add_new_bullet_to_end(existing_text, new_text):
    # Replace whatever the existing bullet was with the matching bullet type
    bullet_type = get_bullet_type(existing_text)
    new_bullet = bullet_type + new_text[1:]

    paragraphs = []
    in_bulleted_list = False
    for line in existing_text.split("\n"):
        if line.startswith(bullet_type):
            in_bulleted_list = True
        else:
            if in_bulleted_list:
                # We've come to the end of the bulleted list, add our new option.
                paragraphs.append(new_bullet)
                in_bulleted_list = False
        paragraphs.append(line)
    if new_bullet not in paragraphs:
        paragraphs.append(new_bullet)
    return "\n".join(paragraphs)
