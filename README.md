This tiny script will serve you as a Telegram data logger.

It will store in the DATABASE called logs.sqlite everything happening on your Telegram account, including:
- table Messages with incoming and outcoming messages from every chat and channel in the and their attributes:
	+ id
        + date
        + to_id
        + text
        + out
        + mentioned
        + media_unread
        + silent
        + post
        + from_id
        - [fwd_from]
        + via_bot_id
        + reply_to_msg_id
        - [media]
        + reply_markup
        + entities
        + views
        + edit_date
        + post_author
        + grouped_id
- table ChatActions (i.e. 'user joined chat') and their attributes:
	+ id
	+ to_id
	+ event_name
	+ date
- table Edited [messages] with attributes:
	+ id
	+ to_id
	+ from_id
	+ message
	+ date
- deleted messages (simply mark corresponding messages from the Messages table as deleted!)
- table UserUpdates (i.e. 'user is online\offline now') and their attributes:
	+ id
	+ username*
	+ first_name*
	+ second_name*
	+ update
	+ date

REQUIREMENTS:
1. python3.7
2. some python modules including but not limited to:
	- telethon
	- sqlite3
	- asyncio

HOW TO USE:
0. register your own telegram application and obtain the api_id; you can do it here: https://core.telegram.org/api/obtaining_api_id
1. run the script.py, but take into account that it will create some additional files in its directory
2. enter requested data (like your telegram app's api_id, api_hash, and your account's phone number & password)
3. enjoy!

P.S. No need to re-enter this data once again after you restart this script, since it creates config and session files
* the script will try to fetch these attributes, that said it can fail
