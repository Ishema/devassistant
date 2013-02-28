import os

import plumbum

from devassistant import argument
from devassistant import assistant_base
from devassistant import exceptions
from devassistant.logger import logger

from devassistant.command_helpers import PathHelper, RPMHelper, YUMHelper

class PythonAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [DjangoAssistant, FlaskAssistant, LibAssistant]

    name = 'python'
    fullname = 'Python'

class DjangoAssistant(PythonAssistant):
    name = 'django'
    fullname = 'Django'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the project (can also be full or relative path)')]

    usage_string_fmt = '{fullname} Assistant lets you create a Django project.'

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.path_exists(self.path)
        if path_exists:
            errors.append('Path exists: {0}'.format(self.path))
        return errors

    def dependencies(self, **kwargs):
        django_rpm = RPMHelper.is_rpm_installed('python-django')
        if not django_rpm:
            if not YUMHelper.install('python-django'):
                raise exceptions.RunException('Failed to install python-django')
            RPMHelper.was_rpm_installed('python-django')

    def run(self, **kwargs):
        django_admin = plumbum.local['django_admin']
        project_path, project_name = os.path.split(self.path)

        logger.info('Creating Django project {name} in {path}...'.format(path=project_path,
                                                                         name=project_name))
        PathHelper.mkdir_p(project_path)
        with plumbum.local.cwd(project_path):
            django_admin('startproject', project_name)
        self._dot_devassistant_create(self.path, **kwargs)
        logger.info('Django project {name} in {path} has been created.'.format(path=project_path,
                                                                               name=project_name))

class FlaskAssistant(PythonAssistant):
    name = 'flask'
    fullname = 'Flask'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the project (can also be full or relative path)')]

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.path_exists(self.path)
        if path_exists:
            errors.append('Path exists: {0}'.format(self.path))
        return errors

    def dependencies(self, **kwargs):
        to_install = []

        # TODO: this should be substituted by a yum group
        for pkg in ['python-flask', 'python-flask-sqlalchemy', 'python-flask-wtf']:
            if not RPMHelper.is_rpm_installed(pkg):
                to_install = []

        if to_install:
            if not YUMHelper.install(*to_install):
                raise exceptions.RunException('Failed to install {0}'.format(' '.join(to_install)))

        for pkg in to_install:
            RPMHelper.was_rpm_installed(pkg)

    def run(self, **kwargs):
        logger.info('Kickstarting a Flask project under {0}'.format(kwargs['name']))
        logger.info('Creating directory structure...')
        PathHelper.mkdir_p(self.path)
        PathHelper.mkdir_p('{0}/static'.format(self.path))
        PathHelper.mkdir_p('{0}/templates'.format(self.path))

        logger.info('Creating initial project files...')
        # the flask template doesn't in fact need rendering, so just copy it
        PathHelper.cp(os.path.join(self.template_dir, 'python', 'flask'),
                      os.path.join(self.path, '__init__.py'))
        self._dot_devassistant_create(self.path, **kwargs)

class LibAssistant(PythonAssistant):
    name = 'lib'
    fullname = 'Python Library'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the library (can also be full or relative path)')]

    usage_string_fmt = '{fullname} Assistant lets you create a custom python library.'

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.path_exists(self.path)
        if path_exists:
            errors.append('Path exists: {0}'.format(self.path))
        return errors

    def dependencies(self, **kwargs):
        st_rpm = RPMHelper.is_rpm_installed('python-setuptools')
        if not st_rpm:
            if not YUMHelper.install('python-setuptools'):
                raise exceptions.RunException('Failed to install python-setuptools')
            RPMHelper.was_rpm_installed('python-setuptools')

    def run(self, **kwargs):
        lib_path, lib_name = os.path.split(self.path)

        logger.info('Creating library project {name} in {path}...'.format(path=lib_path,
                                                                          name=lib_name))
        PathHelper.mkdir_p(self.path)
        with plumbum.local.cwd(self.path):
            PathHelper.mkdir_p(lib_name)
            touch = plumbum.local['touch']
            touch('{0}/__init__.py'.format(lib_name))
            setup_py = self._jinja_env.get_template(os.path.join('python', 'lib', 'setup.py'))
            with open('setup.py', 'w') as f:
                f.write(setup_py.render(name=lib_name))
        self._dot_devassistant_create(self.path, **kwargs)
        logger.info('Library project {name} in {path} has been created.'.format(path=lib_path,
                                                                               name=lib_name))

