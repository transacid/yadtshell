#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2014  Immobilien Scout GmbH
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
        self.write_target_file('it01.domain', 'it02.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain'))
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status frontend-service')\
                .then_return(1)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status backend-service')\
                .then_return(1)
            when.calling('ssh').at_least_with_arguments('it01.domain') \
                .then_return(0)

            when.calling('ssh').at_least_with_arguments('it02.domain').and_input(
                '/usr/bin/yadt-status').then_write(yadt_status_answer.stdout('it02.domain'))
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status frontend-service')\
                .then_return(1)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status backend-service')\
                .then_return(1)
            when.calling('ssh').at_least_with_arguments('it02.domain') \
                .then_return(0)

        status_return_code = self.execute_command('yadtshell status -v')
        stop_return_code = self.execute_command(
            'yadtshell stop service://* -v -p 2')

        with self.verify() as complete_verifier:
            self.assertEqual(0, status_return_code)
            self.assertEqual(0, stop_return_code)

            with complete_verifier.filter_by_argument('it01.domain') as verify:
                verify.called('ssh').at_least_one_argument_matches(
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
                verify.called('ssh').at_least_one_argument_matches(
                    'it01.domain').and_input('/usr/bin/yadt-status')

            with complete_verifier.filter_by_argument('it02.domain') as verify:
                verify.called('ssh').at_least_one_argument_matches(
                    'it02.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', '-O', 'check')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-stop frontend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-status frontend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-stop backend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-status backend-service')
                verify.called('ssh').at_least_one_argument_matches(
                    'it02.domain').and_input('/usr/bin/yadt-status')

            complete_verifier.finished()


if __name__ == '__main__':
    unittest.main()
