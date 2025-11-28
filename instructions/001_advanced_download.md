you see @cms/views/situation/export_download.py .


Let's wrap it in a meta-feature called "Download All", accessible via @cms/templates/cms/situation_list.html.

Loop all [situations](cms/models/situation.py).
For each, loop each possible pair of target+native language.
A pair is only possible if a description of the situation is available in both the native lang and the target lang that was picked; if not, immediately skip.

For each of that loop, run the core download util (just the heart of it, don't actually download. may need refactor.).
Check: After recursively getting all relevant glosses, does the list contain at least one gloss in the picked native lang and at least one in the picked target lang? If not, this situation is also not valid for this pair.

If both these checks path, download the situation with a filename `$id_$target.iso_$native.iso.jsonl`. Also remember it.

After finishing this loop, download more files:
- `native_languages.jsonl`, a list of all languages (iso, name, short) that have at least one valid situation with it as native lang picked
- `target_languages.jsonl`, the same thing for target langs
- loop the valid language pairs
    - for each download another index file with the format `situations_$target.iso_$native.iso.jsonl`
    - Each should contain a list of situations for this combination, logging id, target description, native description, image_link