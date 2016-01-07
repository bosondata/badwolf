# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import git
import requests
from requests.auth import HTTPBasicAuth


class BitbucketAPIError(requests.RequestException):
    """Bitbucket API call error"""
    def __init__(self, code, error, description, *args, **kwargs):
        super(BitbucketAPIError, self).__init__(*args, **kwargs)
        self.code = code
        self.error = error
        self.description = description


class APIDispatcher(object):
    def __init__(self):
        self._session = requests.Session()

    def dispatch(self, method, url, **kwargs):
        raise NotImplementedError()

    def clone_repository(self, full_name, path):
        raise NotImplementedError()

    @property
    def session(self):
        return self._session


class BasicAuthDispatcher(APIDispatcher):
    def __init__(self, username, password):
        super(BasicAuthDispatcher, self).__init__()
        self._username = username
        self._password = password

    def dispatch(self, method, url, **kwargs):
        kwargs['auth'] = HTTPBasicAuth(self._username, self._password)
        return self._session.request(
            method,
            url,
            **kwargs
        )

    def clone_repository(self, full_name, path):
        clone_url = 'https://{username}:{password}@bitbucket.org/{name}.git'.format(
            username=self._username,
            password=self._password,
            name=full_name
        )
        return git.Git().clone(clone_url, path)


class OAuth2Dispatcher(APIDispatcher):
    def __init__(self, oauth_key, oauth_secret):
        super(OAuth2Dispatcher, self).__init__()
        self._oauth_key = oauth_key
        self._oauth_secret = oauth_secret
        self._access_token = None
        self._refresh_token = None

    def get_authorization_url(self, grant_type='code'):
        return 'https://bitbucket.org/site/oauth2/authorize?client_id={key}&response_type={type_}'.format(
            key=self._oauth_key,
            type_=grant_type
        )

    def grant_access_token(self, code):
        res = self._session.post(
            'https://bitbucket.org/site/oauth2/access_token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
            },
            auth=HTTPBasicAuth(self._oauth_key, self._oauth_secret)
        )
        try:
            res.raise_for_status()
        except requests.RequestException as reqe:
            error_info = res.json()
            raise BitbucketAPIError(
                res.status_code,
                error_info.get('error', ''),
                error_info.get('error_description', ''),
                request=reqe.request,
                response=reqe.response
            )
        data = res.json()
        self._access_token = data['access_token']
        self._refresh_token = data['refresh_token']
        self._token_type = data['token_type']
        return data

    def refresh_access_token(self, token=None):
        token = token or self._refresh_token
        res = self._session.post(
            'https://bitbucket.org/site/oauth2/access_token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': token
            },
            auth=HTTPBasicAuth(self._oauth_key, self._oauth_secret)
        )
        try:
            res.raise_for_status()
        except requests.RequestException as reqe:
            error_info = res.json()
            raise BitbucketAPIError(
                res.status_code,
                error_info.get('error', ''),
                error_info.get('error_description', ''),
                request=reqe.request,
                response=reqe.response
            )
        data = res.json()
        self._access_token = data['access_token']
        self._refresh_token = data['refresh_token']
        self._token_type = data['token_type']
        return data

    def dispatch(self, method, url, **kwargs):
        headers = {
            'Authorization': 'Bearer {}'.format(self._access_token),
        }
        kwargs['headers'] = headers
        return self._session.request(method, url, **kwargs)

    def clone_repository(self, full_name, path):
        clone_url = 'https://x-token-auth:{access_token}@bitbucket.org/{name}.git'.format(
            access_token=self._access_token,
            name=full_name
        )
        return git.Git().clone(clone_url, path)


class Bitbucket(object):
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher

    def request(self, method, url, **kwargs):
        if not url.startswith('https://'):
            url = 'https://api.bitbucket.org/{}'.format(url)

        res = self._dispatcher.dispatch(method, url, **kwargs)
        try:
            res.raise_for_status()
        except requests.RequestException as reqe:
            error_info = res.json()
            if res.status_code == 401:
                # Access token expired
                self.refresh_access_token()
                return self.request(method, url, **kwargs)
            else:
                raise BitbucketAPIError(
                    res.status_code,
                    error_info.get('error', ''),
                    error_info.get('error_description', ''),
                    request=reqe.request,
                    response=reqe.response
                )
        return res.json()

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def clone(self, repo_full_name, clone_path):
        return self._dispatcher.clone_repository(repo_full_name, clone_path)
