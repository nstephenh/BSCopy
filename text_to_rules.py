from util.log_util import STYLES, print_styled, get_diff
from util.node_util import get_description
from util.text_gen_utils import errors
from util.system_util import rules_list, get_node_from_system

page_number = "96"
publication_id = "89c5-118c-61fb-e6d8"
first_paragraph_is_flavor = True
raw_text = """
Afterburner
Colossal secondary combustors attached to the main engines of a flyer
allowed this vehicle a surprising burst of speed.
Once per game at the start of the Movement Phase, a model with
this Special Rule may elect to fire its Afterburner. If it does so, the
model may make an additional move after its normal move, up to
its normal movement Characteristic. Note that for this additional
move, the Movement value cannot be modified in any way.
Caestus Prow
The armoured fore of this craft was a masterwork of layered armour,
shield generators, and reinforced bulkheads.
A model with this Special Rule may declare a Ramming attack in
the same manner as a Tank, regardless of its actual unit type. This
attack must be declared at the start of the Movement Phase, after
you have decided whether or not the will fire its Afterburner (if it
has the Afterburner Special Rule). When conducting a Ramming
attack, the hit is automatically resolved at Strength 10, AP 3, and
adds +1 to any rolls on the Vehicle Damage table it inflicts. If the
model fired its Afterburner this turn, add +2 instead.
In addition, the model has an Invulnerable Save of 5+ against any
attacks against its Front Armour, including any damage it suffers
as a result of it Ramming or being Rammed itself.
A model with this Special Rule is immune to the effects of the
Armourbane (Melta) Special Rule – meaning that no extra D6 for
armour penetration can be rolled against the model as a result of
this Special Rule.
Auto-Servo Tracking
Independent firing control subsystems allowed this weapon to track
and fire without requiring their operator to direct them.
A weapon with this Special Rule can fire at a different target to the
other weapons the model is armed with.
Augmetics (X)
Some warriors in the Age of Darkness had extensive amounts of
augmetics within, enough even to survive the most grievous of wounds.
When a model with this Special Rule suffers an unsaved Wound, it
can make a special Augmetics roll to avoid being wounded (this is
not a Saving Throw and so can be used against attacks that state
that ‘no Saves of any kind are allowed’).
Roll a D6 each time an unsaved Wound is suffered. On a result
that is equal to or greater than the value in brackets, the unsaved
Wound is discounted – treat it as having been Saved. On any other
result, the Wound is taken as normal. For example, a unit with the
Augmetics (6+) Special Rule would need to score a 6 in order to
discount a Wound inflicted upon it.
If on any unit this rule is presented simply as Augmetics, without a
value in brackets, then count it as Augmetics (6+).
This is a Damage Mitigation roll – any model may make only a
single Damage Mitigation roll of any type for any given Wound
(see page 174).
Artillery Spotters
These spotters worked in tandem with their charges, calling targets for
those under their command to assail.
A unit with this Special Rule may grant the benefits of a Cognis
Signum it has purchased to a single unit with at least one model
within 6” of a model from this unit, instead of using the benefit
itself.
Note that the unit must be from the same Tercio as it to grant it
the benefits of the Cognis Signum in this way.
Brittle
The sharpened edge on this weapon was impressively good at slicing
through almost any substance - unless the blade bit at a bad angle.
If a model armed with a weapon with this Special Rule hits with all
attacks made with this weapon in a single phase, the blade’s edge is
blunted – at the end of the phase, the weapon’s AP value drops to
AP 4 and it loses any variant of the Rending (X) Special Rule it
possesses for the rest of the battle.
Broken Soul
For those who had already given themselves to the darkness, it was only
a small step to invite the evil within themselves…
A model with this Special Rule may be given the Corrupted
Sub-type at no additional cost in points - this must be decided at
the start of the battle before any models are deployed and may not
be changed during the battle.
Born of Steel
This combatant had become more metal than flesh, and could walk
among automata as one of their own.
A model with this Special Rule may be given the Patris Cybernetica
Special Rule at no additional cost in points - this must be decided
at the start of the battle before any models are deployed and may
not be changed during the battle.
Armoured Superstructure
Approaching in bulk that of a Super-Heavy vehicle, some armoured
behemoths could withstand blows that would utterly destroy a lesser
target.
Whenever a roll is made on the Vehicle Damage Table against a
model with this Special Rule, subtract -1 from the result rolled.
Consul (X)
Despite their lofty station that had otherwise outstripped the rank of
Consul, Astartes Centurions would often retain all the privileges of
their former rank.
A model with this Special Rule is counted as having the named
Legiones Consularis Upgrade as indicated in brackets in the
Special Rule for all intents and purposes, including Rites of War,
Special Rules, and wargear limitations which either require there
to be one to be present in a detachment, or prevent it. Note that
this does not confer any of the benefits normally gained from that
upgrade to the model themselves from any such sources.
    """
output_file = "weapon_output.xml"
final_output = ""
if __name__ == '__main__':

    new_rules = {}
    current_rule = ""
    paragraph_count = 0
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) < 50 and not line.endswith('.'):
            print(f"{line} is likely a special rule")
            current_rule = line
            new_rules[current_rule] = ""
            paragraph_count = 0 if first_paragraph_is_flavor else 1

        # We now know we are inside a rule.

        # Skip this line if it's flavor text.
        print(f"{line} is part of {current_rule}, paragraph {paragraph_count}")
        if paragraph_count >= 1:
            new_rules[current_rule] += line.strip()

        if line[-1] in [".", "…"]:
            if paragraph_count > 0:
                # add linebreaks between paragraphs:
                new_rules[current_rule] += "\n"
            paragraph_count += 1
        else:
            if new_rules[current_rule]:
                new_rules[current_rule] += " "  # Space instead of a line break.

    for rule, rule_text in new_rules.items():
        print(f'\033[1m {rule}\033[0m')

        if rule in rules_list.keys():
            print(f"Rule exists in data files: {rules_list[rule]}")
            node = get_node_from_system(rules_list[rule])
            existing_rules_text = get_description(node)
            diff = get_diff(existing_rules_text, rule_text, 2)
            if diff:
                print_styled("\tText Differs!", STYLES.PURPLE)
                print(diff)
        else:
            print_styled("\tNew Rule!", STYLES.GREEN)
            print(rule_text)

    if len(errors) > 1:
        print("There were one or more errors, please validate the output")
        print(errors)

    f = open(output_file, "a")
    f.write(final_output)
    f.close()
