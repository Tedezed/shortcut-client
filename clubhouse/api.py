import json
import logging
from os import path
from urllib.parse import urlparse

import requests

ENDPOINT_HOST = "https://api.clubhouse.io"
ENDPOINT_PATH = "/api/v3"

logger = logging.getLogger("clubhouse")


class ClubhouseClient(object):
    def __init__(self, api_key, ignored_status_codes=None):
        self.ignored_status_codes = ignored_status_codes or []
        self.api_key = api_key

    def get(self, *segments, **kwargs):
        '''Included for backwards compatibility.
        Not used in versions above 0.3.0.
        '''
        return self._request("get", *segments, **kwargs)

    def post(self, *segments, **kwargs):
        '''Included for backwards compatibility.
        Not used in versions above 0.3.0.
        '''
        return self._request("post", *segments, **kwargs)

    def put(self, *segments, **kwargs):
        '''Included for backwards compatibility.
        Not used in versions above 0.3.0.
        '''
        return self._request("put", *segments, **kwargs)

    def delete(self, *segments, **kwargs):
        '''Included for backwards compatibility.
        Not used in versions above 0.3.0.
        '''
        return self._request("delete", *segments, **kwargs)

    def _request(self, method, data=None, *segments, **kwargs):
        '''An internal helper method for calling any endpoint.

        Args:
            method (str): Must be "get", "post", "put" or "delete"
            data (dict): Can contain any of the body parameters listed in the
                API reference for the endpoint. Defaults to None.
        Returns:
            A response object
        '''

        if not segments[0].startswith(ENDPOINT_PATH):
            segments = [ENDPOINT_PATH, *segments]

        url = path.join(ENDPOINT_HOST, *[str(s).strip("/") for s in segments])

        # See the docs for more details on how the prefix is determined
        # https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse
        prefix = "&" if urlparse(url)[4] else "?"

        headers = {"Content-Type": "application/json"}
        data = json.dumps(data)

        # https://requests.readthedocs.io/en/master/api/#requests.request
        response = requests.request(
            method, url + f"{prefix}token={self.api_key}", headers=headers,
            data=data, **kwargs
        )
        if (
            response.status_code > 299
            and response.status_code not in self.ignored_status_codes
        ):
            logger.error(
                f"Status code: {response.status_code}, Content: {response.text}"
            )
            response.raise_for_status()
        if response.status_code == 204:
            return {}

        return response

    #############
    #  Actions  #
    #############

    def _create_item(self, data, *segments, **kwargs):
        '''An internal helper method for calling any "Create"-related endpoint.

        Args:
            method (str): Must be "get", "post", "put" or "delete"
            data (dict): Can contain any of the body parameters listed in the
                API reference for the endpoint.
        Returns:
            A JSON object containing information about the new item
        '''
        result = self._request("post", data, *segments, **kwargs)
        return result.json()

    def _delete_item(self, *segments, **kwargs):
        '''An internal helper method for calling any "Delete"-related endpoint.

        Returns:
            A JSON object containing information about the updated item
        '''
        result = self._request("delete", None, *segments, **kwargs)
        return result

    def _get_item(self, *segments, **kwargs):
        '''An internal helper method for calling any "Get"-related endpoint.

        Args:
            method (str): Must be "get", "post", "put" or "delete"
            id (int): The requested item's ID
        Returns:
            A JSON object containing information about the requested item
        '''
        result = self._request("get", None, *segments, **kwargs)
        return result.json()

    def _list_items(self, *segments, **kwargs):
        '''An internal helper method for calling any "List"-related endpoint.

        Args:
            method (str): Must be "get"
        Returns:
            A list of dictionaries, where each dictionary is one item
        '''
        result = self._request("get", None, *segments, **kwargs)
        items = result.json()
        while result.next:
            result = self._request("get", None, result.next, **kwargs)
            items.extend(result.json())
        return items

    def _update_item(self, data, *segments, **kwargs):
        '''An internal helper method for calling any "Update"-related endpoint.

        Args:
            data (dict): Can contain any of the body parameters listed in the
                API reference for the endpoint.
        Returns:
            A JSON object containing information about the updated item
        '''
        result = self._request("put", data, *segments, **kwargs)
        return result.json()

    ################
    #  Milestones  #
    ################

    def create_milestone(self, data, **kwargs):
        '''Create a Milestone.
        https://clubhouse.io/api/rest/v3/#Create-Milestone

        Example:
            from clubhouse import ClubhouseClient
            conn = ClubhouseClient(API_KEY)
            conn.create_milestone({'name': 'TEST'})

        Args:
            data (dict): Can contain any of the body parameters listed in the
                API reference linked above as keys.
        Returns:
            A JSON object containing information about the new Milestone.
        '''
        segments = ["milestones"]
        return self._create_item(data, *segments, **kwargs)

    def delete_milestone(self, id, **kwargs):
        '''Delete a specific Milestone.
        https://clubhouse.io/api/rest/v3/#Delete-Milestone

        Example:
            from clubhouse import ClubhouseClient
            conn = ClubhouseClient(API_KEY)
            conn.delete_milestone(123)

        Args:
            id (int): The Milestone ID

        Returns:
            An empty dictionary
        '''
        segments = ["milestones", id]
        return self._delete_item(*segments, **kwargs)

    def get_milestone(self, id, **kwargs):
        '''Retrieve a specific Milestone.
        https://clubhouse.io/api/rest/v3/#Get-Milestone

        Example:
            from clubhouse import ClubhouseClient
            conn = ClubhouseClient(API_KEY)
            conn.get_milestone(123)

        Args:
            id (int): The Milestone ID

        Returns:
            A JSON object containing information about the requested Milestone.
        '''
        segments = ["milestones", id]
        return self._get_item(*segments, **kwargs)

    def list_milestone_epics(self, id, **kwargs):
        '''List all Milestone Epics.
        https://clubhouse.io/api/rest/v3/#List-Milestone-Epics

        Example:
            from clubhouse import ClubhouseClient
            conn = ClubhouseClient(API_KEY)
            conn.list_milestone_epics(123)

        Returns:
            A list of dictionaries, where each dictionary is one Epic of the
            requested Milestone.
        '''
        segments = ["milestones", id, "epics"]
        return self._list_items(*segments, **kwargs)

    def list_milestones(self, **kwargs):
        '''List all Milestones.
        https://clubhouse.io/api/rest/v3/#List-Milestones

        Example:
            from clubhouse import ClubhouseClient
            conn = ClubhouseClient(API_KEY)
            conn.list_milestones()

        Returns:
            A list of dictionaries, where each dictionary is one Milestone.
        '''
        segments = ["milestones"]
        return self._list_items(*segments, **kwargs)

    def update_milestone(self, id, data, **kwargs):
        '''Update a specific Milestone.
        https://clubhouse.io/api/rest/v3/#Update-Milestone

        Example:
            from clubhouse import ClubhouseClient
            conn = ClubhouseClient(API_KEY)
            conn.update_milestone(123)

        Args:
            id (int): The Milestone ID
            data (dict): Can contain any of the body parameters listed in the
                API reference linked above as keys.

        Returns:
            A JSON object containing information about the updated Milestone.
        '''
        segments = ["milestones", id]
        return self._update_item(data, *segments, **kwargs)