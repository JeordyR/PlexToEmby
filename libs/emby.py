"""

4K Movies item id: ec27261a0c809aa017c1c9e0d02c31ac
4K TV Shows item id: fe68e648dcdb7f21053e08c8a036517c

Jeordy ID: 72fd5eb0524744d2ad20bd617195af4a

    {
      "Name": "Anna",
      "ServerId": "2e50f9401ae8483181dfa3a4d567f841",
      "Id": "15",
      "RunTimeTicks": 71396250000,
      "IsFolder": false,
      "Type": "Movie",
      "ImageTags": {
        "Primary": "fde2424fe5ba12cd2a480b1f0814f17a",
        "Logo": "5055ecd314509b89b3534f362431d10c",
        "Thumb": "29a4ecf76a7b892f02e3e18d9338533d"
      },
      "BackdropImageTags": [
        "27678404120f6a80c0bec3c224c39313"
      ],
      "MediaType": "Video"
    },
    {
      "Name": "Aquaman",
      "ServerId": "2e50f9401ae8483181dfa3a4d567f841",
      "Id": "16",
      "RunTimeTicks": 85993920000,
      "IsFolder": false,
      "Type": "Movie",
      "ImageTags": {
        "Primary": "b7c73d2127e51580ffc2f6b6ea5cfd00",
        "Logo": "797cbb8589c2897602f12630e5e4cfa2",
        "Thumb": "18be29abc28b9c8b5181ec19187cc4c4"
      },
      "BackdropImageTags": [
        "214770a2a7bedbe052785e1ce2a2a823"
      ],
      "MediaType": "Video"
    },


curl -X POST "http://10.10.1.1:8096/emby/Users/72fd5eb0524744d2ad20bd617195af4a/PlayedItems/15?api_key=24a1e0a1af924cb88996692933125503" -H "accept: application/json"

"""
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