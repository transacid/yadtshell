import unittest

from mock import Mock, patch

import yadtshell
from yadtshell.util import (inbound_deps_on_same_host,
                            outbound_deps_on_same_host,
                            compute_dependency_scores,
                            calculate_max_tries_for_interval_and_delay,
                            render_state,
                            restore_current_state,
                            get_mtime_of_current_state)
from yadtshell.constants import STANDALONE_SERVICE_RANK


class ServiceOrderingTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}
        self.components = yadtshell.components.ComponentDict()
        self.bar_service = yadtshell.components.Service(
            'foobar42', 'barservice', {})
        self.baz_service = yadtshell.components.Service(
            'foobar42', 'bazservice', {})
        self.ack_service = yadtshell.components.Service(
            'foobar42', 'ackservice', {})

        self.components['service://foobar42/barservice'] = self.bar_service
        self.components['service://foobar42/bazservice'] = self.baz_service
        self.components['service://foobar42/ackservice'] = self.ack_service

    def test_inbound_deps_should_return_empty_list_when_service_is_not_needed(self):

        self.assertEqual(inbound_deps_on_same_host(
            self.bar_service, self.components), [])

    def test_inbound_deps_should_return_needing_service(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']

        self.assertEqual(
            inbound_deps_on_same_host(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_outbound_deps_should_return_empty_list_when_service_needs_nothing(self):
        self.assertEqual(outbound_deps_on_same_host(
            self.bar_service, self.components), [])

    def test_outbound_deps_should_return_needed_service(self):
        self.bar_service.needs = ['service://foobar42/bazservice']

        self.assertEqual(
            outbound_deps_on_same_host(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_should_compute_inbound_deps_recursively(self):
        self.ack_service.needed_by = ['service://foobar42/bazservice']
        self.baz_service.needed_by = ['service://foobar42/barservice']

        self.assertEqual(inbound_deps_on_same_host(self.ack_service, self.components), [
                         'service://foobar42/bazservice', 'service://foobar42/barservice'])

    def test_should_compute_outbound_deps_recursively(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        self.baz_service.needs = ['service://foobar42/ackservice']

        self.assertEqual(outbound_deps_on_same_host(self.bar_service, self.components), [
                         'service://foobar42/bazservice', 'service://foobar42/ackservice'])

    def test_should_label_standalone_services(self):
        compute_dependency_scores(self.components)
        self.assertEqual(
            self.baz_service.dependency_score, STANDALONE_SERVICE_RANK)

    def test_should_increase_dependency_score_when_ingoing_edge_found(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, 1)

    def test_should_decrease_dependency_score_when_outdoing_edge_found(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, -1)

    def test_should_enable_and_decrease_dependency_score_based_on_edges(self):
        self.bar_service.needs = ['service://foobar42/bazservice']      # -1
        self.baz_service.needs = ['service://foobar42/ackservice']      # -1
        self.bar_service.needed_by = ['service://foobar42/ackservice']  # +1
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, -1)

    def test_should_ignore_cross_host_inward_dependencies(self):
        self.components['service://otherhost/foo'] = yadtshell.components.Service(
            'otherhost', 'foo', {})
        self.bar_service.needed_by = ['service://otherhost/foo']
        compute_dependency_scores(self.components)

    def test_should_ignore_cross_host_outward_dependencies(self):
        self.components['service://otherhost/foo'] = yadtshell.components.Service(
            'otherhost', 'foo', {})
        self.bar_service.needs = ['service://otherhost/foo']
        compute_dependency_scores(self.components)
        self.assertEqual(
            self.bar_service.dependency_score, STANDALONE_SERVICE_RANK)


class IntervalAndDelayConversionTests(unittest.TestCase):

    def test_should_return_divisor_when_division_without_remainder_is_possible(self):
        max_tries = calculate_max_tries_for_interval_and_delay(10, 5)

        self.assertEqual(max_tries, 2)

    def test_should_increase_interval_when_remainder_found(self):
        max_tries = calculate_max_tries_for_interval_and_delay(10, 6)

        self.assertEqual(max_tries, 2)  # now waits 12 seconds instead of 10

    def test_should_at_least_make_one_try_when_delay_is_longer_than_interval(self):
        max_tries = calculate_max_tries_for_interval_and_delay(1, 5)

        self.assertEqual(max_tries, 1)

    def test_should_not_make_tries_when_interval_is_zero(self):
        max_tries = calculate_max_tries_for_interval_and_delay(0, 5)

        self.assertEqual(max_tries, 0)


class ServiceRenderingTests(unittest.TestCase):

    def setUp(self):
        self.mock_term = Mock()
        self.mock_render = Mock(side_effect=lambda unrendered: unrendered)
        yadtshell.settings.term = self.mock_term
        yadtshell.settings.term.render = self.mock_render

    def test_should_render_red_when_state_is_down(self):
        render_state(yadtshell.settings.DOWN, width=0)

        self.mock_render.assert_called_with('${RED}${BOLD}down${NORMAL}')

    def test_should_render_green_when_state_is_up(self):
        render_state(yadtshell.settings.UP, width=0)

        self.mock_render.assert_called_with('${GREEN}${BOLD}up${NORMAL}')

    def test_should_adjust_left_by_default(self):
        render_state(yadtshell.settings.UP, width=4)

        self.mock_render.assert_called_with('${GREEN}${BOLD}up  ${NORMAL}')

    def test_should_adjust_right(self):
        render_state(yadtshell.settings.UP, width=6, just='right')

        self.mock_render.assert_called_with('${GREEN}${BOLD}    up${NORMAL}')


class CurrentStateTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.OUT_DIR = '/out/dir/'

    @patch('yadtshell.util.os.path.getmtime')
    def test_should_return_mtime_of_current_state(self, mtime_function):
        get_mtime_of_current_state()

        mtime_function.assert_called_with('/out/dir/current_state.components')

    @patch('yadtshell.util.restore')
    def test_should_restore_current_state(self, restore_function):
        restore_current_state()

        restore_function.assert_called_with('/out/dir/current_state.components')

    @patch('yadtshell.util.logger')
    @patch('yadtshell.util.restore')
    @patch('yadtshell.util.sys')
    def test_should_exit_when_restore_fails(self, sys, restore, _):
        def fail(_):
            raise IOError()
        restore.side_effect = fail

        restore_current_state()

        sys.exit.assert_called_with(1)
