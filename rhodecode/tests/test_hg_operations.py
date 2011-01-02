# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_hg_operations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test suite for making push/pull operations
    
    :created_on: Dec 30, 2010
    :copyright: (c) 2010 by marcink.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""

import os
import shutil
import logging

from subprocess import Popen, PIPE

from os.path import join as jn

from rhodecode.tests import TESTS_TMP_PATH, NEW_HG_REPO, HG_REPO

USER = 'test_admin'
PASS = 'test12'
HOST = '127.0.0.1:5000'

log = logging.getLogger(__name__)


class Command(object):

    def __init__(self, cwd):
        self.cwd = cwd

    def execute(self, cmd, *args):
        """Runs command on the system with given ``args``.
        """

        command = cmd + ' ' + ' '.join(args)
        log.debug('Executing %s' % command)
        print command
        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, cwd=self.cwd)
        stdout, stderr = p.communicate()
        print stdout, stderr
        return stdout, stderr


#===============================================================================
# TESTS
#===============================================================================
def test_clone():
    cwd = path = jn(TESTS_TMP_PATH, HG_REPO)

    try:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        #print 'made dirs %s' % jn(path)
    except OSError:
        raise


    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s %(dest)s' % \
                  {'user':USER,
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':path}

    stdout, stderr = Command(cwd).execute('hg clone', clone_url)

    assert """adding file changes""" in stdout, 'no messages about cloning'
    assert """abort""" not in stderr , 'got error from clone'



def test_clone_anonymous_ok():
    cwd = path = jn(TESTS_TMP_PATH, HG_REPO)

    try:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        #print 'made dirs %s' % jn(path)
    except OSError:
        raise


    clone_url = 'http://%(host)s/%(cloned_repo)s %(dest)s' % \
                  {'user':USER,
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':path}

    stdout, stderr = Command(cwd).execute('hg clone', clone_url)
    print stdout, stderr
    assert """adding file changes""" in stdout, 'no messages about cloning'
    assert """abort""" not in stderr , 'got error from clone'

def test_clone_wrong_credentials():
    cwd = path = jn(TESTS_TMP_PATH, HG_REPO)

    try:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        #print 'made dirs %s' % jn(path)
    except OSError:
        raise


    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s %(dest)s' % \
                  {'user':USER + 'error',
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':path}

    stdout, stderr = Command(cwd).execute('hg clone', clone_url)

    assert """abort: authorization failed""" in stderr , 'no error from wrong credentials'


def test_pull():
    pass

def test_push():

    modified_file = jn(TESTS_TMP_PATH, HG_REPO, 'setup.py')
    for i in xrange(5):
        cmd = """echo 'added_line%s' >> %s""" % (i, modified_file)
        Command(cwd).execute(cmd)

        cmd = """hg ci -m 'changed file %s' %s """ % (i, modified_file)
        Command(cwd).execute(cmd)

    Command(cwd).execute('hg push %s' % jn(TESTS_TMP_PATH, HG_REPO))

def test_push_new_file():

    test_clone()

    cwd = path = jn(TESTS_TMP_PATH, HG_REPO)
    added_file = jn(path, 'setup.py')

    Command(cwd).execute('touch %s' % added_file)

    Command(cwd).execute('hg add %s' % added_file)

    for i in xrange(15):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        Command(cwd).execute(cmd)

        cmd = """hg ci -m 'commited new %s' %s """ % (i, added_file)
        Command(cwd).execute(cmd)

    push_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s' % \
                  {'user':USER,
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':jn(TESTS_TMP_PATH, HG_REPO)}

    Command(cwd).execute('hg push %s' % push_url)

def test_push_wrong_credentials():

    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s' % \
                  {'user':USER + 'xxx',
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':jn(TESTS_TMP_PATH, HG_REPO)}

    modified_file = jn(TESTS_TMP_PATH, HG_REPO, 'setup.py')
    for i in xrange(5):
        cmd = """echo 'added_line%s' >> %s""" % (i, modified_file)
        Command(cwd).execute(cmd)

        cmd = """hg ci -m 'commited %s' %s """ % (i, modified_file)
        Command(cwd).execute(cmd)

    Command(cwd).execute('hg push %s' % clone_url)

def test_push_wrong_path():
    cwd = path = jn(TESTS_TMP_PATH, HG_REPO)
    added_file = jn(path, 'somefile.py')

    try:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        print 'made dirs %s' % jn(path)
    except OSError:
        raise

    Command(cwd).execute("""echo '' > %s""" % added_file)
    Command(cwd).execute("""hg init %s""" % path)
    Command(cwd).execute("""hg add %s""" % added_file)

    for i in xrange(2):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        Command(cwd).execute(cmd)

        cmd = """hg ci -m 'commited new %s' %s """ % (i, added_file)
        Command(cwd).execute(cmd)

    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s' % \
                  {'user':USER,
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO + '_error',
                   'dest':jn(TESTS_TMP_PATH, HG_REPO)}

    stdout, stderr = Command(cwd).execute('hg push %s' % clone_url)
    assert """abort: HTTP Error 403: Forbidden"""  in stderr


if __name__ == '__main__':
    test_clone()
    test_clone_wrong_credentials()
    ##test_clone_anonymous_ok()

    #test_push_new_file()
    #test_push_wrong_path()
    #test_push_wrong_credentials()


