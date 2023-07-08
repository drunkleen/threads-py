import re
import json
import urllib
import random
import requests
from datetime import datetime
from typing import List, Optional

from threadspy.types import (
    Thread,
    UsersData,
    ThreadsUser,
    ThreadData,
    GetUserProfileResponse,
    GetThreadLikersResponse,
    GetUserProfileThreadResponse,
    GetUserProfileRepliesResponse,
    GetUserProfileThreadsResponse,
)

DEFAULT_LSD_TOKEN = "NjppQDEgONsU_1LCzrmp6q"
DEFAULT_DEVICE_ID = f"android-{random.randint(0, 1e24):x}"


class ThreadsAPI:
    fbLSDToken = DEFAULT_LSD_TOKEN
    verbose = False
    noUpdateLSD = False
    username = None
    password = None
    device_id = DEFAULT_DEVICE_ID
    http_client = requests.Session()

    def __init__(
        self,
        verbose=None,
        noUpdateLSD=None,
        fbLSDToken=None,
        username=None,
        password=None,
        device_id=None,
    ):
        if fbLSDToken is not None and "<class 'str'>" == str(type(fbLSDToken)):
            self.fbLSDToken = fbLSDToken
        if username is not None and "<class 'str'>" == str(type(username)):
            self.username = username
        if password is not None and "<class 'str'>" == str(type(password)):
            self.password = password
        if device_id is not None and "<class 'str'>" == str(type(device_id)):
            self.device_id = device_id
        if noUpdateLSD is not None and "<class 'bool'>" == str(type(noUpdateLSD)):
            self.noUpdateLSD = noUpdateLSD
        if verbose is not None and "<class 'bool'>" == str(type(verbose)):
            self.verbose = verbose

    def __get_default_headers(self, username: str = None):
        if username is None:
            return {
                "authority": "www.threads.net",
                "accept": "*/*",
                "accept-language": "ko,en;q=0.9,ko-KR;q=0.8,ja;q=0.7",
                "cache-control": "no-cache",
                "origin": "https://www.threads.net",
                "pragma": "no-cache",
                "referer": None,
                "x-asbd-id": "129477",
                "x-fb-lsd": self.fbLSDToken,
                "x-ig-app-id": "238260118697367",
            }
        else:
            self.username = username
            return {
                "authority": "www.threads.net",
                "accept": "*/*",
                "accept-language": "ko,en;q=0.9,ko-KR;q=0.8,ja;q=0.7",
                "cache-control": "no-cache",
                "origin": "https://www.threads.net",
                "pragma": "no-cache",
                "referer": f"https://www.threads.net/@{username}",
                "x-asbd-id": "129477",
                "x-fb-lsd": self.fbLSDToken,
                "x-ig-app-id": "238260118697367",
            }

    def get_user_id_from_username(self, username) -> str:
        """
        Returns user id by username.

        Args:
            username (str): username on threads.net

        Returns:
            str: a user id.
        """
        headers = self.__get_default_headers(username)
        headers[
            "accept"
        ] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        headers["accept-language"] = "ko,en;q=0.9,ko-KR;q=0.8,ja;q=0.7"
        headers["pragma"] = "no-cache"
        headers["referer"] = "https://www.instagram.com/"
        headers["sec-fetch-dest"] = "document"
        headers["sec-fetch-mode"] = "navigate"
        headers["sec-fetch-site"] = "cross-site"
        headers["sec-fetch-user"] = "?1"
        headers["upgrade-insecure-requests"] = "1"
        headers["x-asbd-id"] = None
        headers["x-fb-lsd"] = None
        headers["x-ig-app-id"] = None
        response = self.http_client.get(f"https://www.instagram.com/{username}", headers=headers)

        text = response.text.replace("\n", "")

        user_id_match = re.search('"user_id":"(\d+)",', text)
        user_id = user_id_match.group(1) if user_id_match else None

        lsd_token_match = re.search('"LSD",\[\],{"token":"(\w+)"},\d+\]', text)
        lsd_token = lsd_token_match.group(1) if lsd_token_match else None

        if not self.noUpdateLSD and self.fbLSDToken is not None:
            self.fbLSDToken = lsd_token
            if self.verbose:
                print("[fbLSDToken] UPDATED", self.fbLSDToken)

        return user_id

    def get_user_profile(self, username, user_id=None) -> ThreadsUser:
        """
        Returns profile info by username.

        Args:
            username (str): username on threads.net
            user_id (str, optional):: user_id which is unique to each user.

        Returns:
            ThreadsUser: a profile info.
        """
        if self.verbose:
            print("[fbLSDToken] USING", self.fbLSDToken)

        if not user_id:
            user_id = self.get_user_id_from_username(username)
        headers = self.__get_default_headers(username)
        headers["x-fb-friendly-name"] = "BarcelonaProfileRootQuery"

        params = {
            "lsd": self.fbLSDToken,
            "variables": f'{{"userID":"{user_id}"}}',
            "doc_id": "23996318473300828",
        }

        response = self.http_client.post(
            "https://www.threads.net/api/graphql", params=params, headers=headers
        )

        try:
            user = GetUserProfileResponse.from_dict(response.json())
            return user.data.userData.user
        except Exception as e:
            if self.verbose:
                print("[ERROR] ", e)
            return ThreadsUser(
                pk="",
                full_name="",
                profile_pic_url="",
                follower_count=0,
                is_verified=False,
                username="",
                profile_context_facepile_users=None,
                id=None,
            )

    def get_user_profile_threads(self, username: str, user_id: str) -> List[Thread]:
        """
        Returns a list of threads posted in the profile.

        Args:
            username (str): username on threads.net
            user_id (str): user_id which is unique to each user.

        Returns:
            List[Thread]: list of threads posted in the profile.
        """
        if self.verbose:
            print("[fbLSDToken] USING", self.fbLSDToken)
        headers = self.__get_default_headers(username)
        headers["x-fb-friendly-name"] = "BarcelonaProfileThreadsTabQuery"

        params = {
            "lsd": f"{self.fbLSDToken}",
            "variables": f'{{"userID":"{user_id}"}}',
            "doc_id": "6232751443445612",
        }

        response = self.http_client.post(
            "https://www.threads.net/api/graphql", params=params, headers=headers
        )

        try:
            threads = GetUserProfileThreadsResponse.from_dict(response.json())
            return threads.data.mediaData.threads
        except Exception as e:
            if self.verbose:
                print("[ERROR] ", e)
            return []

    def get_user_profile_replies(self, username: str, user_id: str) -> List[Thread]:
        """
        Returns a list of replies in the thread.

        Args:
            username (str): username on threads.net
            user_id (str): user_id which is unique to each user.

        Returns:
            List[Thread]: list of replies in the thread.
        """
        if self.verbose:
            print("[fbLSDToken] USING", self.fbLSDToken)
        headers = self.__get_default_headers(username)
        headers["x-fb-friendly-name"] = "BarcelonaProfileRepliesTabQuery"

        params = {
            "lsd": f"{self.fbLSDToken}",
            "variables": f'{{"userID":"{user_id}"}}',
            "doc_id": "6684830921547925",
        }

        response = self.http_client.post(
            "https://www.threads.net/api/graphql", params=params, headers=headers
        )

        try:
            replies = GetUserProfileRepliesResponse.from_dict(response.json())
            return replies.data.mediaData.threads
        except Exception as e:
            if self.verbose:
                print("[ERROR] ", e)
            return []

    def get_post_id_from_thread_id(self, thread_id: str) -> str:
        """
        Returns a thread info from thread id.

        Args:
            thread_id (str): thread_id which is unique to each thread.

        Returns:
            str: a post id
        """
        thread_id = thread_id.split("?")[0]
        thread_id = thread_id.replace("/", "")
        post_url = f"https://www.threads.net/t/{thread_id}"
        result = self.get_post_id_from_url(post_url=post_url)
        return result

    def get_post_id_from_url(self, post_url) -> str:
        """
        Returns the post_id of a specific one thread.

        Args:
            post_url (str): a threads app direct link

        Returns:
            str: a post id
        """
        response = requests.get(post_url)
        text = response.text
        text = text.replace("\n", "")
        post_id_match = re.search(r'{"post_id":"(.*?)"', text)
        post_id = post_id_match.group(1) if post_id_match else None

        lsd_token_match = re.search(r'"LSD",\[\],{"token":"(\w+)"},\d+\]', text)
        lsd_token = lsd_token_match.group(1) if lsd_token_match else None

        if not self.noUpdateLSD and self.fbLSDToken is not None:
            self.fbLSDToken = lsd_token
            if self.verbose:
                print("[fbLSDToken] UPDATED", self.fbLSDToken)
        return post_id

    def get_threads(self, post_id: str) -> ThreadData:
        """
        Returns a thread info from post id.

        Args:
            post_id (str): post_id which is unique to each post.

        Returns:
            ThreadData: a thread info
        """
        if self.verbose:
            print("[fbLSDToken] USING", self.fbLSDToken)
        headers = self.__get_default_headers()
        headers["x-fb-friendly-name"] = "BarcelonaPostPageQuery"

        params = {
            "lsd": f"{self.fbLSDToken}",
            "variables": f'{{"postID":"{post_id}"}}',
            "doc_id": "5587632691339264",
        }

        response = self.http_client.post(
            "https://www.threads.net/api/graphql", params=params, headers=headers
        )

        try:
            thread = GetUserProfileThreadResponse.from_dict(response.json())
            return thread.data.data
        except Exception as e:
            if self.verbose:
                print("[ERROR] ", e)
            return ThreadData(containing_thread=None, reply_threads=[])

    def get_thread_likers(self, post_id: str) -> UsersData:
        """
        Returns a thread likers

        Args:
            post_id (str): post_id which is unique to each post.

        Returns:
            UsersData: a thread likers
        """
        if self.verbose:
            print("[fbLSDToken] USING", self.fbLSDToken)
        headers = self.__get_default_headers()

        params = {
            "lsd": f"{self.fbLSDToken}",
            "variables": f'{{"mediaID":"{post_id}"}}',
            "doc_id": "9360915773983802",
        }

        response = self.http_client.post(
            "https://www.threads.net/api/graphql", params=params, headers=headers
        )

        try:
            thread = GetThreadLikersResponse.from_dict(response.json())
            return thread.data.likers
        except Exception as e:
            if self.verbose:
                print("[ERROR] ", e)
            return UsersData(users=[])

    def get_token(self) -> Optional[str]:
        """
        Returns fb login token

        Returns:
            str: a token
        """
        if self.username is None or self.password is None:
            return None
        base = "https://i.instagram.com/api/v1"
        url = f"{base}/bloks/apps/com.bloks.www.bloks.caa.login.async.send_login_request/"
        blockVersion = "5f56efad68e1edec7801f630b5c122704ec5378adbee6609a448f105f34a9c73"
        headers = {
            "User-Agent": "Barcelona 289.0.0.77.109 Android",
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        params = json.dumps(
            {
                "client_input_params": {
                    "password": self.password,
                    "contact_point": self.username,
                    "device_id": self.device_id,
                },
                "server_params": {
                    "credential_type": "password",
                    "device_id": self.device_id,
                },
            }
        )
        bk_client_context = json.dumps({"bloks_version": blockVersion, "styles_id": "instagram"})
        payload = f"params={urllib.parse.quote(params)}&bk_client_context={urllib.parse.quote(bk_client_context)}&bloks_versioning_id={blockVersion}"
        payload = payload.replace("%20", "")
        response = requests.post(url, timeout=60 * 1000, headers=headers, data=payload)
        data = response.text
        if data == "Oops, an error occurred.":
            return None
        pos = data.split("Bearer IGT:2:")[1]
        pos = pos.split("==")[0]
        token = f"{pos}=="
        return token

    def publish(self, caption: str) -> bool:
        """
        Returns fb login token

        Returns:
            str: a token
        """
        if self.username is None or self.password is None:
            return False

        user_id = self.get_user_id_from_username(self.username)
        if user_id is None:
            return False
        token = self.get_token()
        if token is None:
            return False
        base = "https://i.instagram.com"
        url = f"{base}/api/v1/media/configure_text_only_post/"
        params = json.dumps(
            {
                "publish_mode": "text_post",
                "text_post_app_info": '{"reply_control":0}',
                "timezone_offset": "-25200",
                "source_type": "4",
                "_uid": user_id,
                "device_id": str(self.device_id),
                "caption": caption,
                "upload_id": str(int(datetime.now().timestamp() * 1000)),
                "device": {
                    "manufacturer": "OnePlus",
                    "model": "ONEPLUS+A3010",
                    "android_version": 25,
                    "android_release": "7.1.1",
                },
            }
        )
        payload = f"signed_body=SIGNATURE.{urllib.parse.quote(params)}"
        payload = payload.replace("%20", "")

        headers = {
            "Authorization": f"Bearer IGT:2:{token}",
            "User-Agent": "Barcelona 289.0.0.77.109 Android",
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            if self.verbose:
                print("[ERROR] ", e)
            return False
