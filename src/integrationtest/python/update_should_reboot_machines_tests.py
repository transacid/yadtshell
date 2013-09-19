#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2013  Immobilien Scout GmbH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Maximilien Riehl'

import unittest
import integrationtest_support

import yadt_status_answer


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file('it01.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain', reboot_required_to_activate_latest_kernel=True))
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status frontend-service').then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-host-update -r yit-config-it01-0:0.0.1-2').then_return(255)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status backend-service').then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain') \
                .then_return(0)

        actual_return_code = self.execute_command('yadtshell update -v --reboot')

        self.assertEqual(0, actual_return_code)

        with self.verify() as verify:
            verify.called('ssh').at_least_with_arguments(
                'it01.domain').and_input('/usr/bin/yadt-status')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', '-O', 'check')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-stop frontend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status frontend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-stop backend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status backend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-host-update -r yit-config-it01-0:0.0.1-2')

            verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command uptime')

            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-start backend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status backend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-start frontend-service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status frontend-service')

            verify.called('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status')

if __name__ == '__main__':
    unittest.main()
