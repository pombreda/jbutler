#
# Copyright (c) SAS Institute Inc.
#


import os
import sys

from jbutler import butlercfg, errors
from jbutler.jenkinsapi import jenkins
from jbutler.lib import jobs
import mock

from .. import jbutlerhelp


class DeleteJobsTests(jbutlerhelp.JButlerHelper):
    '''
    Tests for jobs delete
    '''
    def setUp(self):
        jbutlerhelp.JButlerHelper.setUp(self)

        self.foo_filename = os.path.join(self.workDir, 'jobs', 'foo.xml')

        self.mkdirs('jobs')
        self.mkfile(self.foo_filename, contents='A foo job')

        self.cfg = butlercfg.ButlerConfiguration()
        self.cfg.server = 'http://example.com'

        self.jobDir = os.path.join(self.workDir, 'jobs')

        self.Jenkins_patcher = mock.patch(
            'jbutler.utils.jenkins_utils.Jenkins')
        self.Jenkins = self.Jenkins_patcher.start()
        self.Jenkins.return_value = mock.MagicMock(spec=jenkins.Jenkins)

        self.sys_patcher = mock.patch('jbutler.lib.jobs.sys')
        self.sys = self.sys_patcher.start()
        self.sys.stdout = mock.MagicMock(spec=sys.stdout)

    def tearDown(self):
        self.Jenkins_patcher.stop()
        self.sys_patcher.stop()
        jbutlerhelp.JButlerHelper.tearDown(self)

    def test_delete_jobs(self):
        self.Jenkins.return_value.has_job.return_value = True

        expected = [self.foo_filename]
        actual = jobs.deleteJobs(
            self.cfg, [self.foo_filename])

        self.assertEqual(actual, expected)
        self.assertTrue(os.path.exists(self.foo_filename))
        self.Jenkins.return_value.delete_job.assert_called_once_with('foo')

    def test_delete_jobs_multiple(self):
        bar_filename = os.path.join(self.workDir, 'jobs', 'bar.xml')
        self.mkfile(bar_filename, contents='A bar job')

        self.Jenkins.return_value.has_job.side_effect = (True, True)

        expected = [self.foo_filename, bar_filename]
        actual = jobs.deleteJobs(
            self.cfg,
            [self.foo_filename, bar_filename],
            )

        self.assertEqual(actual, expected)
        self.assertTrue(os.path.exists(self.foo_filename))
        self.assertTrue(os.path.exists(bar_filename))
        self.assertEqual(
            self.Jenkins.return_value.has_job.call_args_list,
            [mock.call('foo'), mock.call('bar')],
            )
        self.assertEqual(
            self.Jenkins.return_value.delete_job.call_args_list,
            [mock.call('foo'), mock.call('bar')],
             )

    def test_delete_jobs_force(self):
        self.Jenkins.return_value.has_job.return_value = True

        expected = [self.foo_filename]
        actual = jobs.deleteJobs(self.cfg, [self.foo_filename], self.jobDir)

        self.assertEqual(actual, expected)
        self.assertFalse(os.path.exists(self.foo_filename))
        self.Jenkins.return_value.delete_job.assert_called_once_with('foo')

    def test_delete_jobs_missing_job(self):
        bar_filename = os.path.join(self.workDir, 'jobs', 'bar.xml')
        self.mkfile(bar_filename, contents='A bar job')

        self.Jenkins.return_value.has_job.side_effect = (True, False)

        expected = [self.foo_filename]
        actual = jobs.deleteJobs(
            self.cfg,
            [self.foo_filename, bar_filename],
            )

        self.assertEqual(actual, expected)
        self.assertTrue(os.path.exists(self.foo_filename))
        self.assertEqual(
            self.Jenkins.return_value.has_job.call_args_list,
            [mock.call('foo'), mock.call('bar')],
            )
        self.Jenkins.return_value.delete_job.assert_called_once_with('foo')
        self.sys.stdout.write.assert_called_once_with(
            "warning: job does not exist on server: 'bar'\n")

    def test_delete_jobs_missing_job_config(self):
        bar_filename = os.path.join(self.workDir, 'jobs', 'bar.xml')

        self.Jenkins.return_value.has_job.return_value = (True, True)

        self.assertRaises(
            errors.CommandError,
            jobs.deleteJobs,
            self.cfg,
            [self.foo_filename, bar_filename],
            )

        self.assertTrue(os.path.exists(self.foo_filename))
        self.Jenkins.return_value.delete_job.assert_called_once_with('foo')
