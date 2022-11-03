Run generate_template_from_base.py to make a template 


Run map_cats to map most of the root entries for each cat file.

For each cat file:
* Edit the library tags on units listed in the manually mapping section of the map_cats file. 
These are all files that have multiple entries with the same name and hidden value.
* Get the ID for the selection entry group for warlord traits from the template
* Get the ID for the selection entry group for retinue from the template
* Add this comment to the selection entry group for warlord traits ```<comment>    template_id_{from_above}</comment>```
* Add this comment to the selection entry group for retinue: ```<comment>    template_id_{from_above}</comment>```
