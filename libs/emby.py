import json

import requests


def get_users(server: str, api_key: str) -> list:
    uri = f"{server}/emby/Users"

    params = {"IsDisabled": False, "api_key": api_key}

    response = requests.get(uri, params=params, verify=False)

    return json.loads(response.content)


class Emby:
    def __init__(self, server: str, api_key: str, user_id: str):
        self.server = server
        self.api_key = api_key
        self.user = user_id

    def find_section(self, section_name: str) -> str:
        uri = f"{self.server}/emby/Library/MediaFolders"

        params = {"api_key": self.api_key}

        response = requests.get(uri, params=params, verify=False)

        data = json.loads(response.content)

        section_id = ""
        for item in data["Items"]:
            if section_name.lower() == item["Name"].lower():
                section_id = item["Id"]
                break

        return section_id

    def find_item_id(self, provider: str, provider_id: str, section_id: str) -> str:
        uri = f"{self.server}/emby/Items"

        params = {"ParentId": section_id, "AnyProviderIdEquals": f"{provider}.{provider_id}", "api_key": self.api_key}

        response = requests.get(uri, params=params, verify=False)

        data = json.loads(response.content)

        if data.get("Items") and isinstance(data["Items"], list):
            return data["Items"][0]["Id"]
        else:
            return ""

    def get_show_episodes(self, section_id: str, show_id: str) -> dict:
        episodes = {}

        uri = f"{self.server}/emby/Shows/{show_id}/Episodes"

        params = {"ParentId": section_id, "api_key": self.api_key}

        response = requests.get(uri, params=params, verify=False)

        data = json.loads(response.content)

        if data.get("Items") and isinstance(data["Items"], list):
            for item in data["Items"]:
                if not item["ParentIndexNumber"] in episodes.keys():
                    episodes[item["ParentIndexNumber"]] = {}

                episodes[item["ParentIndexNumber"]][item["IndexNumber"]] = item["Id"]

        return episodes

    def mark_item_watched(self, item_id):
        uri = f"{self.server}/emby/Users/{self.user}/PlayedItems/{item_id}?api_key={self.api_key}"

        requests.post(uri, verify=False)