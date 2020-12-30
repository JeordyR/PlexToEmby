# PlexToEmby

Basic script to sync the watched status of all items in Plex (for all users) into Emby (for all users).

This intendend as a migration tool, not something to run consistently to keep items in sync. It only works from Plex -> Emby and just shoves all watched items in Plex as watched in Emby with no special logic.

Tested with a server with a PlexPass user and several managed users (invited friends, not home users), not sure how it would fare in other conditions.

The library/section names in Plex and Emby must match for this to work currently. The check is case-insenstivie, so "TV Shows" on Plex and "Tv Shows" on Emby would still match. Any Plex libraries not matched to an Emby library will be skipped.

### How To Use

Clone or download this repo to your machine.

Install the required packages:

`pip install -r requirements.txt`

You can also use pipenv or something similar:

```
pip install pipenv
pipenv run python -m pip install -r requirements.txt
pipenv run python PlexToEmby.py
```

Then run the script `python PlexToEmby.py`

On first run you will be prompted for your Plex account and password for authentication as well your Emby server URL and API key. This information will be stored in a file called Auth.json for future runs.


### Configuration

There is not much configurability. There are 2 global variables in the PlexToEmby.py file you can update to filter down what is getting synced if desired:

* SECTIONS_TO_SYNC: List of Plex section names that should be synced, will ignore all others if anything is populated here.
* USERS_TO_SYNC: List of users (by mapped name if setup) to sync, will ignore all others if anything is populated here.


### Mapping Plex Users to Emby Users

A file can be created called UserMappings.json to map the name of the managed users in Plex to their user in Emby if they are different. If this file is not present it will assume the user's name in Plex matches their name in Emby perfectly. If the file is specified, all users that need to be handled must be specified, even if some of them have matching names. File just needs to be standard json format with a single dict where the keys are the Emby name and the values are the Plex name.

Example:
```json
{
    "John": "plexnameshowingasemail@gmail.com",
    "Jane": "Some Plex Name",
}
```

### Refresh/Change Authentication

If you have already run the script and have an Auth.json file present, you can either delete that file and run it again to go through the auth setup process again, or run setup_auth.py directly and it will go through the setup and replace the Auth.json file with the new values.