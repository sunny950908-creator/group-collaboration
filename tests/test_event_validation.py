"""Protocol examples and malformed JSON values, independent of Git workflows."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from groupctl import Error, validate


EXAMPLES = {
    'change_published': dict(change_id='C-17', branch='people/P17/work', commit='abc',
        summary='', files_changed=['app.py'], interface_changes=[], tests_run=[],
        known_issues=[], proposed_for_integration=True),
    'finding': dict(summary='Finding', evidence=['Reproduced']),
    'question': dict(question_id='Q-1', text='Question', blocking=False),
    'answer': dict(question_id='Q-1', text='Answer'),
    'review': dict(change_id='C-17', verdict='accept', summary='Review', issues=[], tests_run=[]),
    'test_result': dict(scope='current_branch', commit='abc', commands=['python check.py'],
        automated_result='pass', passed=1, failed=0, skipped=0,
        human_checks_required=[], summary='Passed'),
    'integration_result': dict(change_id='C-17', target_branch='people/P17/work',
        result='success', merge_commit='abc', conflicts=[], conflict_resolution_summary='',
        verification=dict(build='pass', tests='pass', semantic_review='pass'), summary='Merged'),
    'blocker': dict(summary='Blocked', blocking_change_id='C-17', requested_action='Review'),
    'final_candidate': dict(canonical_commit='abc', candidate_report_path='candidate.md',
        test_evidence=[{'event_id': 'E-test'}], known_issues=[]),
    'final_result': dict(canonical_commit='abc', final_report_path='final.md',
        test_evidence=['E-test'], known_limitations=[], initiated_by='P17'),
}


def example(kind):
    return dict(protocol_version='0.1', event_id='E-test', event_type=kind,
                group_id='G01', person_id='P17', created_at='2026-10-16T07:00:00Z',
                related_events=[], **copy.deepcopy(EXAMPLES[kind]))


class EventValidation(unittest.TestCase):
    def test_protocol_examples_and_optional_extensions(self):
        for kind in EXAMPLES:
            with self.subTest(kind=kind):
                event = example(kind)
                event['vendor_extension'] = {'arbitrary': [None, 7, False]}
                validate(event)
        # A name used by another event is still an extension here.
        event = example('question')
        event['summary'] = {'vendor_detail': 1}
        validate(event)

    def test_required_text_fields_reject_non_strings(self):
        for kind in EXAMPLES:
            event = example(kind)
            for field, value in event.items():
                if not isinstance(value, str):
                    continue
                for bad in (None, 1, False, [], {}):
                    with self.subTest(kind=kind, field=field, bad=bad):
                        malformed = copy.deepcopy(event)
                        malformed[field] = bad
                        with self.assertRaisesRegex(Error, field + ' must be a string'):
                            validate(malformed)

    def test_string_lists_reject_wrong_container_and_elements(self):
        for kind in EXAMPLES:
            event = example(kind)
            for field, value in event.items():
                if not isinstance(value, list) or field == 'test_evidence':
                    continue
                for bad in (None, 'text', {}, 1):
                    with self.subTest(kind=kind, field=field, container=bad):
                        malformed = copy.deepcopy(event)
                        malformed[field] = bad
                        with self.assertRaisesRegex(Error, field + ' must be an array'):
                            validate(malformed)
                for bad in (None, 1, False, [], {}):
                    with self.subTest(kind=kind, field=field, element=bad):
                        malformed = copy.deepcopy(event)
                        malformed[field] = ['valid', bad]
                        with self.assertRaisesRegex(Error, field + r'\[1\] must be a string'):
                            validate(malformed)

    def test_non_object_events(self):
        for bad in (None, [], 'event', 1, True):
            with self.subTest(bad=bad), self.assertRaisesRegex(Error, 'Event must be an object'):
                validate(bad)

    def test_timestamp_errors(self):
        for value, message in [('invalid', 'valid ISO timestamp'),
                               ('2026-10-16T07:00:00', 'timezone')]:
            event = example('finding')
            event['created_at'] = value
            with self.subTest(value=value), self.assertRaisesRegex(Error, message):
                validate(event)

    def test_verification_values_are_text_without_new_enums(self):
        for field in ('build', 'tests', 'semantic_review'):
            for bad in (None, 1, False, [], {}):
                event = example('integration_result')
                event['verification'][field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaisesRegex(
                        Error, 'verification.' + field + ' must be a string'):
                    validate(event)
        event['verification'][field] = 'extension-status'
        validate(event)
        for bad in (None, [], 'pass', {}, {'build': 'pass'}):
            event = example('integration_result')
            event['verification'] = bad
            with self.subTest(verification=bad), self.assertRaisesRegex(Error, 'Incomplete verification'):
                validate(event)

    def test_existing_required_fields_enums_and_numeric_rules(self):
        event = example('review')
        del event['summary']
        with self.assertRaisesRegex(Error, 'Missing field: summary'):
            validate(event)
        event = example('review')
        event['verdict'] = 'unknown'
        with self.assertRaisesRegex(Error, 'Invalid verdict'):
            validate(event)
        for field, bad in [('passed', True), ('failed', -1), ('skipped', '0')]:
            event = example('test_result')
            event[field] = bad
            with self.subTest(field=field), self.assertRaises(Error):
                validate(event)
        event = example('question')
        event['blocking'] = 1
        with self.assertRaisesRegex(Error, 'blocking must be boolean'):
            validate(event)


if __name__ == '__main__':
    unittest.main()
