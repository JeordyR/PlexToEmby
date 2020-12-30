import json
import os

from libs import emby
from plexapi.myplex import MyPlexAccount


def setup_auth(force: bool = False) -> dict:
    """
    Get authentication information for Plex account and all managed users.
    Get and store the Emby connection details, API key, and user list with their IDs.

    :param force: Flag to force full refresh of credentials, overwriting existing Auth.json file, defaults to False
    :type force: bool, optional
    :return: Dict with all of the credentials, API key, and URLs pulled from Auth.json
    :rtype: dict
    """
    auth_info = {}

    if os.path.exists("Auth.json") and not force:
        with open("Auth.json") as f:
            auth_info = json.loads(f.read())
    else:
        if not force:
            print("No authentication information present, running auth setup...")

        plex_auth = get_plex_auth()
        emby_auth = get_emby_auth()

        # Store base URLs
        auth_info["PLEX_URL"] = plex_auth.get("BASE_URL", "")
        auth_info["EMBY_URL"] = emby_auth.get("BASE_URL", "")
        auth_info["EMBY_API_KEY"] = emby_auth.get("API_KEY", "")

        # Put auth_info together from plex and emby auth info, use user mappings if present.
        if os.path.exists("UserMappings.json"):
            user_mappings = {}
            with open("UserMappings.json") as f:
                user_mappings = json.loads(f.read())

            for user, plex_user in user_mappings.items():
                auth_info[user] = {}
                auth_info[user]["Plex"] = plex_auth.get(plex_user, "")
                auth_info[user]["Emby"] = emby_auth.get(user, "")
        else:
            for plex_user, plex_token in plex_auth.items():
                auth_info[plex_user] = {"Plex": plex_token, "Emby": emby_auth.get(plex_user, "")}

        with open("Auth.json", "w") as f:
            f.write(json.dumps(auth_info, sort_keys=True, indent=4))

        print(
            (
                "\n\nAuthentication information loaded for Plex and Emby, delete the Auth.json file "
                "or run setup_auth directly to reset/refresh."
            )
        )

    return auth_info


def get_plex_auth() -> dict:
    """
    Fetch plex token for server user and all managed users.

    :return: Dict with all users and their tokens, key = username value = token + BASE_URL
    :rtype: dict
    """
    auth_info = {}

    while True:
        print("\n\n-- Plex --")

        username = input("Please enter your Plex username: ")
        password = input("Please enter your Plex password: ")
        servername = input("Now enter the server name: ")

        try:
            account = MyPlexAccount(username, password)
        except Exception as e:
            print(f"\nFailed to connect to account {username} with error: {str(e)}, try again...")
            continue

        try:
            plex = account.resource(servername).connect()  # returns a PlexServer instance
        except Exception as e:
            print(f"\nFailed to connect to server {servername} with error: {str(e)}, try again...")
            continue

        break

    auth_info[username] = plex._token
    auth_info["BASE_URL"] = plex._baseurl

    users = account.users()

    if users:
        managed_users = []
        print("\nManaged user(s) found:")

        for user in users:
            if user.friend is True:
                managed_users.append(user.title)
                print(user.title)

        print("\nLoading credentials for users...")

        for user in managed_users:
            try:
                auth_info[user] = account.user(user).get_token(plex.machineIdentifier)
            except Exception as e:
                print(f"Failed to get token for {user} with error: {str(e)}")

    return auth_info


def get_emby_auth() -> dict:
    """
    Gets Emby server endpoint and API key from user, then pulls the list of users configured in Emby and their IDs.

    :return: Dict with user(key) -> id(value) mapping and BASE_URL and API_KEY fields.
    :rtype: dict
    """
    auth_info = {}

    while True:
        print("\n\n-- Emby --")

        server = input("Please enter Emby server URL (IE: http://10.10.1.1:8096): ")
        api_key = input("Please enter your API key for Emby: ")

        try:
            users = emby.get_users(server, api_key)
            break
        except Exception as e:
            print(f"Failed to auth against Emby server {server} with error: {str(e)}, try again...")
            continue

    auth_info["BASE_URL"] = server
    auth_info["API_KEY"] = api_key

    print("\nLoading credentials for users...")

    if users:
        print("\nFound users:")

        for user in users:
            auth_info[user["Name"]] = user["Id"]
            print(user["Name"])

    return auth_info


if __name__ == "__main__":
    print("Setup Auth run manually, forcing refresh of credentials.")
    setup_auth(force=True)
