# BSCopy

BScopy is a set of scripts used to manipulate data in battlescribe/new recruit .cat files.

There are two main cases:
* Creating weapon or unit entries (selection entries) from raw text
* Coping changes from one .cat file to another

## Parse raw text into the proper xml format.
Most of the code for this is set up specifically for [Horus Heresy 2.0](https://github.com/BSData/horus-heresy/)

There are two scripts to run. Both share the following lines of code which are essentially configuration settings:
```python
page_number = "23"
publication_id = "89c5-118c-61fb-e6d8"
raw_text = """ 
INSERT TEXT HERE
"""
output_file = "unit_output.xml"
```
* **output_file**: The name of the file where the generated XML will be appended. I recommend leaving this as the default. 
* **page_number**: The page number from the publication source of the data.
* **publication_id**: The battlescribe id of the publication entry in the game's dataset.
* **raw_text**: a multiline string with specific formatting requirements for each script. See below.

After running each script, you will want to manually copy-paste the generated entries into the end of the shared selection entry list in the XML file. 
Make a minor change in your data editor to re-save the file and clean up the spacing/formatting.

You will need python3 installed, but no other dependencies. Run each script in the command line as below, 
or with an IDE such as PyCharm
```bash
python3 text_to_weapons.py
```

### [text_to_weapons.py](text_to_weapons.py)
This script takes a list of weapons, and creates a selection entry for each. It uses the following format:
```python
raw_text = """
Weapon name <range> <strength> <ap> <type and list of special rules>
Examples:
Three Word Name 12-96“ 7 5 Heavy 5, Barrage, Blast (3”), Pinning, Rending (5+)
Regular Name 24“ 5 4 Rapid Fire, Ignores Cover
Regular Name 24“ 5 4 Rapid Fire 2, Ignores Cover
shortname - +3 - Melee, Overload (6+), Sudden Strike (3)
"""
```
When running it, I found it easiest to paste all the weapon entries from a page in, a block at a time, 
and then run the script to add to the output, changed the page number, and then proceeded to the next block, 
pasting the output after doing all the entries in a publication.

If the message `There were one or more errors, please validate the above` prints, then something went wrong,
likely a special rule was not found. Ensure the special rule is in the game's files. 

### [text_to_unit.py](text_to_unit.py)
This script takes a unit entry in the following format, and a couple additional options:
```python
from system_constants import fast_attack_force_org

force_org = fast_attack_force_org # whatever force_org slot you need, just ensure it's imported properly.

base_points = 160 # points from the unit name

access_points = ""  # Not adding automatic handling for this.
raw_text = """
UNIT NAME IN ALL CAPS (will be converted to titlecase)
Model Name 7 4 4 4 4 2 4 2 7 4+
Different Model Name 7 4 4 4 4 2 4 3 8 4+

Unit Composition
● 4 Model Name
● 1 Different Model Name
Unit Type
● Model Name: Infantry (Subtype)
● Different Model Name: Infantry
(Subtype, Character)
Wargear
● Wargear List
● More wargear
● Wargear Carbine

Special Rules
● Special rules
● Really long special rule name
that got split on multiple lines

Options:
● A UNIT NAME IN ALL CAPS may include:
- Up to 5 additional Model Name.....................................................+25 points per model
● One Model Name may take a:
- Wargear (any shared selection entry) ...........................................................................................................................+5 points
● The unit may be equipped with any of the following:
- Wargear ....................................................................................................................+30 points
- Other Wargear .................................................................................................................+30 points
● Any model in the unit may exchange their Wargear Carbine for one of the following:
- Wargear A and Wargear B ...................................................................................+5 points
- Common Weapon Name .................................................................................................................+5 points
● The Other Model Name may take one of the following:
- Taser GOAT..........................................................................................................................+5 points
"""
```
The above example is for a non-vehicle unit, but vehicles also work.

Copy-pasting from PDFs doesn't generally want to read all the text from the page at once, so instead you should copy in chunks. 
Generally the chunks are Name, statlines, and everything else. The base points, force organization slot, 
and access points for vehicles need to be added to the respective variables.

The script looks for the named sections, and then splits those options by the ● character into entries it can search.
The Special rules section can be omitted and the script will compensate, but leaving out any other section will cause issues.
Because the script splits on the ● character, long special rule names, wargear, or unit subtypes that drop to the next line are tolerated.

The points per model defined in the options list (looks for `may include`) are used in conjunction with the unit cost 
to set the points for any non-"may take extra" model. In the above example, it will be set to 60. 

Options lists are parsed by the ● character per list, and the `-` character per option on the list, with  any number of 
`.` characters separating the points and the option. They look for shared selection entries from any .cat or .gst)
 and group them into Selection Entry Groups, and have the following behavior:
* Per-model points are read, as described above. Those lines don't get checked for wargear
* Option titles containing `and/or` are assumed to have max 2 entries instead of max 1.
* Option titles containing `Any model` or the model name are assumed to be model-specific, and will be added to the selection entry of each model instead of the unit.
  * Any entries starting with `One` ignore this rule, and are placed on the unit.
* Option titles containing `echange` will remove whatever wargear is in the title from that model's default wargear, and add it to the selection entry group for this option list for this model instead.
  * It will be the first link or selection entry in that group and will set defaultAmount to 1 or 2.
    * Note that if it is set to 2, you will likely need to manually change it to 1 and add the other `and/or` option.
  * If there are multiple option titles that could exchange the wargear item, you will have the merge them by hand. This script can only do so much! But it will remind you in the error output.
* Options lines that end in `each` (other than the model lines) will need to have a 'multiply by number of models' 
modifier set manually. Again, the script you will remind you.

As with the weapon script, you can then copy this into the Shared Selection Entry section in your file.

## Copy changes from one file to another
The copying function of BSCopy was set up originally, to copy the shared selection entry links from a template file 
to the 18 space marine legions of horus heresy, before all the legion-specific units (and rite of war changes?) were added.
It likely needs some tweaks now to ensure it does not overwrite any changes and as such **I WOULD NOT RECOMMEND USING IT WITHOUT TESTING**


It assumes that the only changes you want to copy are selection entry links.
This is generally the case when there is one library cat file and multiple files using entries from each of them
(with visibility or category changes only).


For instructions on how to use the copying functionality as of when we synced all the legion units,
please refer to [changes_for_hh_files.md](changes_for_hh_files.md)


## This is awesome, I'd love to use it for *game name here*
Cool! You'll probably need to manually edit a lot of the code, to mirror the format of whatever system your coming from. 
Reach out to `@nstephenh` in the BSData Discord: [![Chat on Discord](https://img.shields.io/discord/558412685981777922.svg?logo=discord&style=popout-square)](https://www.bsdata.net/discord)

## Other Scripts:
### [ensure_links_point_properly.py](ensure_links_point_properly.py)
If you've forked a repo, then you need to change the IDs for the gst and each cat file. 
This script can be run to notify you if any of the cat files ID's need to be changed 
and updates any catalogue links referencing the old IDs. 
### [sync_revisions_with_upstream.py](sync_revisions_with_upstream.py)
If you've forked a repo, and you are trying to pull changes from the upstream repo into your local repo, 
you will likely have some conflicts. This script's goal is to make conflicts easier to spot as you can keep your 
branch's revision numbers identical to the source repo.
