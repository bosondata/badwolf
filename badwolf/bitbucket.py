# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

import git
import requests
from requests.auth import HTTPBasicAuth
from optionaldict import optionaldict


logger = logging.getLogger(__name__)


class BitbucketAPIError(requests.RequestException):
    """Bitbucket API call error"""
    def __init__(self, code, error, description, *args, **kwargs):
        super(BitbucketAPIError, self).__init__(*args, **kwargs)
        self.code = code
        self.error = error
        self.description = description

    def __repr__(self):
        return "BitbucketAPIError({}, '{}', '{}')".format(
            self.code,
            self.error,
            self.description
        )

    def __str__(self):
        return 'code: {}, error: {}, description: {}'.format(
            self.code,
            self.error,
            self.description
        )


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

    def get_git_url(self, full_name):
        return 'https://{username}:{password}@bitbucket.org/{name}.git'.format(
            username=self._username,
            password=self._password,
            name=full_name
        )

    def clone_repository(self, full_name, path, **kwargs):
        clone_url = self.get_git_url(full_name)
        return git.Git().clone(clone_url, path, **kwargs)


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

    def get_git_url(self, full_name):
        return 'https://x-token-auth:{access_token}@bitbucket.org/{name}.git'.format(
            access_token=self._access_token,
            name=full_name
        )

    def clone_repository(self, full_name, path, **kwargs):
        clone_url = self.get_git_url(full_name)
        return git.Git().clone(clone_url, path, **kwargs)


class Bitbucket(object):
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher

    def request(self, method, url, **kwargs):
        if not url.startswith('https://'):
            url = 'https://api.bitbucket.org/{}'.format(url)

        raw = kwargs.pop('raw', False)
        res = self._dispatcher.dispatch(method, url, **kwargs)
        res.encoding = 'utf-8'
        try:
            res.raise_for_status()
        except requests.RequestException as reqe:
            if res.status_code == 401 and isinstance(self._dispatcher, OAuth2Dispatcher):
                # Access token expired
                self.refresh_access_token()
                return self.request(method, url, **kwargs)
            else:
                try:
                    error_info = res.json()
                except (TypeError, ValueError):
                    error_info = {}
                    logger.exception('Extract bitbucket error info failed, response: %s', res.text)

                raise BitbucketAPIError(
                    res.status_code,
                    error_info.get('error', ''),
                    error_info.get('error_description', ''),
                    request=reqe.request,
                    response=reqe.response
                )

        if raw:
            return res
        return res.json()

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)

    def put(self, url, **kwargs):
        return self.request('PUT', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def clone(self, repo_full_name, clone_path, **kwargs):
        return self._dispatcher.clone_repository(repo_full_name, clone_path, **kwargs)

    def get_git_url(self, repo_full_name):
        return self._dispatcher.get_git_url(repo_full_name)


class BuildStatus(object):
    def __init__(self, client, repo, revision, key, url):
        self.client = client
        self.repo = repo
        self.revision = revision
        self.key = key
        self.url = url

    def get(self):
        endpoint = '2.0/repositories/{repo}/commit/{revision}/statuses/build/{key}'.format(
            repo=self.repo,
            revision=self.revision,
            key=self.key
        )
        return self.client.get(endpoint)

    def update(self, state, name=None, description=None):
        endpoint = '2.0/repositories/{repo}/commit/{revision}/statuses/build'.format(
            repo=self.repo,
            revision=self.revision
        )
        return self.client.post(
            endpoint,
            data={
                'key': self.key,
                'state': state,
                'url': self.url,
                'name': name,
                'description': description,
            }
        )


class PullRequest(object):
    def __init__(self, client, repo):
        self.client = client
        self.repo = repo

    def get(self, id):
        endpoint = '2.0/repositories/{repo}/pullrequests/{id}'.format(
            repo=self.repo,
            id=id
        )
        return self.client.get(endpoint)

    def merge(self, id, message):
        endpoint = '2.0/repositories/{repo}/pullrequests/{id}/merge'.format(
            repo=self.repo,
            id=id
        )
        return self.client.post(
            endpoint,
            data={
                'message': message,
            }
        )

    def comment(self, id, content, line_from=None, line_to=None, parent_id=None,
                filename=None, anchor=None, dest_rev=None):
        endpoint = '1.0/repositories/{repo}/pullrequests/{id}/comments'.format(
            repo=self.repo,
            id=id
        )
        data = optionaldict(
            content=content,
            line_from=line_from,
            line_to=line_to,
            parent_id=parent_id,
            filename=filename,
            anchor=anchor,
            dest_rev=dest_rev,
        )
        return self.client.post(endpoint, data=data)

    def comments(self, id, page=1, size=100):
        endpoint = '2.0/repositories/{repo}/pullrequests/{id}/comments'.format(
            repo=self.repo,
            id=id
        )
        params = {
            'page': page,
            'pagelen': size,
        }
        return self.client.get(endpoint, params=params)

    def all_comments(self, id):
        rs = []
        res = self.comments(id)
        rs.extend(res['values'])
        while res.get('next'):
            res = self.comments(id, page=res['page'] + 1)
            rs.extend(res['values'])
        return rs

    def delete_comment(self, id, comment_id):
        endpoint = '1.0/repositories/{repo}/pullrequests/{id}/comments/{cid}'.format(
            repo=self.repo,
            id=id,
            cid=comment_id,
        )
        return self.client.delete(endpoint)

    def diff(self, id):
        from unidiff import PatchSet

        endpoint = '2.0/repositories/{repo}/pullrequests/{id}/diff'.format(
            repo=self.repo,
            id=id
        )
        res = self.client.get(endpoint, raw=True)
        res.encoding = 'utf-8'
        patch = PatchSet(res.text.split('\n'))
        return patch


class Changesets(object):
    def __init__(self, client, repo):
        self.client = client
        self.repo = repo

    def comment(self, node, content, line_from=None, line_to=None,
                parent_id=None, filename=None):
        endpoint = '1.0/repositories/{repo}/changesets/{node}/comments'.format(
            repo=self.repo,
            node=node,
        )
        data = optionaldict(
            content=content,
            line_from=line_from,
            line_to=line_to,
            parent_id=parent_id,
            filename=filename,
        )
        return self.client.post(endpoint, data=data)


class Hooks(object):
    def __init__(self, client, repo):
        self.client = client
        self.repo = repo

    def add(self, name, url, events=None):
        endpoint = '2.0/repositories/{repo}/hooks'.format(
            repo=self.repo,
        )
        data = optionaldict(
            url=url,
            description=name,
            events=events,
            active=True
        )
        return self.client.post(endpoint, json=data)

    def list(self):
        endpoint = '2.0/repositories/{repo}/hooks'.format(
            repo=self.repo,
        )
        return self.client.get(endpoint)


class FlaskBitbucket(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.client = Bitbucket(BasicAuthDispatcher(
            app.config['BITBUCKET_USERNAME'],
            app.config['BITBUCKET_PASSWORD']
        ))

    def request(self, method, url, **kwargs):
        return self.client.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url, **kwargs):
        return self.client.post(url, **kwargs)

    def put(self, url, **kwargs):
        return self.client.put(url, **kwargs)

    def delete(self, url, **kwargs):
        return self.client.delete(url, **kwargs)

    def clone(self, repo_full_name, clone_path, **kwargs):
        return self.client.clone(repo_full_name, clone_path, **kwargs)

    def get_git_url(self, repo_full_name):
        return self.client.get_git_url(repo_full_name)
