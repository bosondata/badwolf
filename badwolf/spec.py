# -*- coding: utf-8 -*-
import io
import base64
import logging
import shlex

import yaml
try:
    from yaml import CLoader as _Loader
except ImportError:
    from yaml import Loader as _Loader
from flask import render_template
from marshmallow import Schema, fields, pre_load, post_load, ValidationError, validate
from marshmallow.utils import is_collection
from marshmallow_oneofschema import OneOfSchema

from badwolf.utils import ObjectDict, to_text, to_binary
from badwolf.security import SecureToken
from badwolf.exceptions import InvalidSpecification


logger = logging.getLogger(__name__)


class ListField(fields.List):
    def _deserialize(self, value, attr, data):
        if not is_collection(value):
            value = [value]

        result = []
        errors = {}
        for idx, each in enumerate(value):
            try:
                result.append(self.container.deserialize(each))
            except ValidationError as e:
                if e.data is not None:
                    result.append(e.data)
                errors.update({idx: e.messages})

        if errors:
            raise ValidationError(errors, data=result)

        return result


class SetField(ListField):
    def _deserialize(self, value, attr, data):
        return set(super(SetField, self)._deserialize(value, attr, data))


class SecureField(fields.String):
    def _deserialize(self, value, attr, data):
        if isinstance(value, dict) and 'secure' in value:
            value = self._decrypt(value['secure'])
        else:
            value = super(SecureField, self)._deserialize(value, attr, data)
        return value

    def _decrypt(self, token):
        from cryptography.fernet import InvalidToken

        try:
            return SecureToken.decrypt(token)
        except InvalidToken:
            logger.warning('Invalid secure token: %s', token)
            return ''


class ObjectDictSchema(Schema):
    @post_load
    def _postprocess(self, data):
        return ObjectDict(data)


class EmailNotificationSchema(ObjectDictSchema):
    recipients = ListField(fields.Email(), load_from='recipients', missing=list)
    on_success = fields.String(missing='never', validate=validate.OneOf(('always', 'never')))
    on_failure = fields.String(missing='always', validate=validate.OneOf(('always', 'never')))

    @pre_load
    def _preprocess(self, data):
        email = {}
        if isinstance(data, dict):
            email = data
        elif isinstance(data, (tuple, list)):
            email['recipients'] = data
        else:
            email['recipients'] = [data]
        return email


class SlackWebHookSchema(ObjectDictSchema):
    webhooks = ListField(SecureField(), load_from='webhooks', missing=list)
    on_success = fields.String(missing='always', validate=validate.OneOf(('always', 'never')))
    on_failure = fields.String(missing='always', validate=validate.OneOf(('always', 'never')))

    @pre_load
    def _preprocess(self, slack):
        webhook = {}
        if isinstance(slack, dict):
            webhook = slack
        elif isinstance(slack, (tuple, list)):
            webhook['webhooks'] = slack
        else:
            webhook['webhooks'] = [slack]
        return webhook


class NotificationSchema(ObjectDictSchema):
    email = fields.Nested(EmailNotificationSchema, load_from='email')
    slack_webhook = fields.Nested(SlackWebHookSchema, load_from='slack_webhook')


class LinterSchema(Schema):
    name = fields.String(missing=None)
    pattern = fields.String(missing=None)

    def __init__(self, *args, **kwargs):
        super(LinterSchema, self).__init__(*args, **kwargs)
        self.__additional_values = {}

    @pre_load
    def _preprocess(self, linter):
        info = {}
        if isinstance(linter, dict):
            name = linter.pop('name', None)
            pattern = linter.pop('pattern', None)
            self.__additional_values = linter
        else:
            name = linter
            pattern = None

        info['name'] = name.strip() if name else None
        info['pattern'] = pattern
        return info

    @post_load
    def _postprocess(self, data):
        data.update(self.__additional_values)
        return ObjectDict(data)


class DeployProviderSchema(ObjectDictSchema):
    provider = fields.String()
    branch = SetField(fields.String(), missing=set)  # 开启部署的 git 分支，空则不触发部署
    tag = fields.Boolean(missing=False)  # 是否开启 git tag 的部署


class ScriptDeploySchema(DeployProviderSchema):
    script = ListField(SecureField())


class PypiDeploySchema(DeployProviderSchema):
    username = SecureField()
    password = SecureField()
    repository = SecureField(missing='https://pypi.python.org/pypi')
    distributions = fields.String(missing='dist/*')


class AnyDeploySchema(OneOfSchema):
    type_field = 'provider'
    type_field_remove = False
    type_schemas = {
        'script': ScriptDeploySchema,
        'pypi': PypiDeploySchema,
    }


class SpecificationSchema(Schema):
    class Meta:
        strict = True

    image = fields.String(missing=None)
    dockerfile = fields.String(missing='Dockerfile')
    docker = fields.Boolean(missing=False)
    privileged = fields.Boolean(missing=False)
    services = ListField(fields.String(), load_from='service', missing=list)
    branch = SetField(fields.String(), missing=set)
    environments = ListField(SecureField(), load_from='env', missing=list)
    scripts = ListField(SecureField(), load_from='script', missing=list)
    after_success = ListField(SecureField(), missing=list)
    after_failure = ListField(SecureField(), missing=list)
    notification = fields.Nested(NotificationSchema)
    linters = fields.Nested(LinterSchema, load_from='linter', many=True, missing=list)
    deploy = ListField(fields.Nested(AnyDeploySchema), missing=list)
    after_deploy = ListField(SecureField(), missing=list)

    @pre_load
    def _preprocess(self, data):
        linters = data.get('linter')
        if linters:
            if not isinstance(linters, (tuple, list)):
                data['linter'] = [linters]
        return data

    @post_load
    def _postprocess(self, data):
        image = data['image']
        if image and ':' not in image:
            # Ensure we have tag name in image
            image = image + ':latest'
        data['image'] = image

        env_map_list = []
        for _env in data['environments']:
            envs = _env.split()
            env_map = {}
            for env_str in envs:
                key, val = env_str.split('=', 1)
                env_map[key] = val
            env_map_list.append(env_map)
        data['environments'] = env_map_list
        return data


class Specification(object):
    def __init__(self):
        self.image = None
        self.services = []
        self.scripts = []
        self.dockerfile = 'Dockerfile'
        self.docker = False  # Bind Docker sock to container or not
        self.after_success = []
        self.after_failure = []
        self.notification = ObjectDict(
            email=None,
            slack_webhook=None,
        )
        self.branch = set()
        self.environments = []
        self.linters = []
        self.privileged = False
        self.deploy = []
        self.after_deploy = []

    @classmethod
    def parse_file(cls, path):
        try:
            if hasattr(path, 'read') and callable(path.read):
                # File-like obj
                conf = yaml.load(path.read(), Loader=_Loader)
            else:
                with io.open(path) as f:
                    conf = yaml.load(f.read(), Loader=_Loader)
        except yaml.error.MarkedYAMLError as e:
            raise InvalidSpecification(str(e))

        return cls.parse(conf)

    @classmethod
    def parse(cls, conf):
        schema = SpecificationSchema()
        try:
            parsed = schema.load(conf)
        except ValidationError as e:
            logger.exception('badwolf specification validation error')
            raise InvalidSpecification(str(e))
        data = parsed.data
        spec = cls()
        for key, value in data.items():
            setattr(spec, key, value)
        return spec

    def is_branch_enabled(self, branch):
        if not self.branch:
            return True
        return branch in self.branch

    @property
    def shell_script(self):
        def _trace(command):
            return 'echo + {}\n{} '.format(
                shlex.quote(command),
                command
            )

        commands = []
        after_success = [_trace(cmd) for cmd in self.after_success]
        after_failure = [_trace(cmd) for cmd in self.after_failure]
        for service in self.services:
            commands.append(_trace('service {} start'.format(service)))
        for script in self.scripts:
            commands.append(_trace(script))

        command_encoded = shlex.quote(to_text(base64.b64encode(to_binary('\n'.join(commands)))))
        context = {
            'command': command_encoded,
            'after_success': '    \n'.join(after_success),
            'after_failure': '    \n'.join(after_failure),
        }
        script = render_template('script.sh', **context)
        logger.debug('Build script: \n%s', script)
        return script
