#!/bin/bash

SCRIPT_DIR=`dirname $0`
ROOT_DIR=`cd $SCRIPT_DIR/.. && pwd`

ENVSPEC=`stat -c %Y $ROOT_DIR/tests/environment.pip`
ENVTIME=`test -d $ROOT_DIR/.ve && stat -c %Y $ROOT_DIR/.ve`

set -e

cd $ROOT_DIR
if [ $ENVSPEC -gt 0$ENVTIME ]; then
    # Setup environment
    virtualenv --no-site-packages $ROOT_DIR/.ve
    source $ROOT_DIR/.ve/bin/activate
    pip install -r $ROOT_DIR/tests/environment.pip
    touch $ROOT_DIR/.ve
else
    source $ROOT_DIR/.ve/bin/activate
fi

# pylint
pylint --rcfile=$ROOT_DIR/.pylintrc django_any > pylint.out || echo 'PyLint done'
tail -n5 pylint.out

# Run tests
python <<EOF
from django import conf
from django.core import management

__name__ = 'django_any.tests'
class TestSettings(conf.UserSettingsHolder):
   INSTALLED_APPS=('django.contrib.auth',
                   'django.contrib.contenttypes',
                   'django_any',
                   'django_nose')
   DATABASE_ENGINE='sqlite3'
   TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
   NOSE_ARGS = ['django_any',
                '--with-coverage',
                '--cover-package=django_any',
                '--with-xunit',
                '--with-xcoverage']

conf.settings.configure(TestSettings(conf.global_settings))
management.call_command('test', 'django_any')
EOF

