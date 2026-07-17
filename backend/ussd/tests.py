from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import Role, User
from elections.models import Election, Position, VotingChannel, VoterEligibility
from candidates.models import Candidate
from system.models import SystemSetting, FeatureFlag
from ussd.models import USSDSession, USSDRequestLog
from voting.models import Vote


@override_settings(DEBUG=True, CELERY_TASK_ALWAYS_EAGER=True)
class USSDWebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSetting.objects.update_or_create(
            key='ussd_enabled',
            defaults={'value': 'true', 'category': 'integrations'},
        )
        SystemSetting.objects.update_or_create(
            key='ussd_service_code',
            defaults={'value': '*928*013#', 'category': 'integrations'},
        )
        FeatureFlag.objects.update_or_create(
            key='ussd_voting',
            defaults={'is_enabled': True, 'category': 'voting'},
        )
        role, _ = Role.objects.get_or_create(name='student', defaults={'description': 'Student'})
        self.voter = User.objects.create_user(
            email='ussd.voter@example.com',
            password='pass12345',
            phone_number='233501234567',
            role=role,
            index_number='BC/ITS/24/USSD',
            onboarding_completed=True,
        )
        admin_role, _ = Role.objects.get_or_create(name='admin', defaults={'description': 'Admin'})
        self.admin = User.objects.create_user(
            email='ussd.admin@example.com',
            password='pass12345',
            role=admin_role,
        )
        self.election = Election.objects.create(
            title='USSD Test Election',
            status='open',
            allow_ussd_voting=True,
            created_by=self.admin,
        )
        self.position = Position.objects.create(
            election=self.election,
            title='President',
            display_order=1,
            is_votable=True,
        )
        self.candidate = Candidate.objects.create(
            election=self.election,
            position=self.position,
            full_name='Alice Candidate',
            status='approved',
            ballot_number=1,
        )
        VotingChannel.objects.get_or_create(channel_name='ussd', defaults={'is_active': True})
        VoterEligibility.objects.create(
            election=self.election,
            user=self.voter,
            is_eligible=True,
        )
        self.url = '/api/v1/ussd/callback/'
        self.index = 'BC/ITS/24/USSD'
        self.phone = '233501234567'
        self.user_id = 'R3ETNHCMVR_LOHp'

    def _arkesel(self, **overrides):
        body = {
            'sessionID': 'arkesel-sess',
            'userID': self.user_id,
            'newSession': True,
            'msisdn': self.phone,
            'userData': '*928*013#',
            'network': 'MTN',
        }
        body.update(overrides)
        return self.client.post(self.url, body, format='json')

    def test_arkesel_welcome_json(self):
        response = self._arkesel(sessionID='sess-welcome')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'application/json')
        data = response.json()
        self.assertEqual(data['sessionID'], 'sess-welcome')
        self.assertEqual(data['userID'], self.user_id)
        self.assertEqual(data['msisdn'], self.phone)
        self.assertTrue(data['continueSession'])
        self.assertIn('INDEX', data['message'].upper())
        self.assertFalse(data['message'].startswith('CON '))
        self.assertEqual(USSDSession.objects.count(), 1)
        self.assertEqual(USSDRequestLog.objects.count(), 1)

    def test_arkesel_subsequent_user_data_is_latest_input(self):
        sid = 'sess-svt'
        self._arkesel(sessionID=sid, newSession=True, userData='*928*013#')
        r2 = self._arkesel(
            sessionID=sid,
            newSession=False,
            userData=self.index,
        )
        data = r2.json()
        if not data.get('continueSession'):
            self.fail(f'Expected continueSession; got {data}')
        self.assertTrue(data['continueSession'])
        self.assertIn('SVT', data['message'].upper())
        session = USSDSession.objects.filter(provider_session_id=sid).first()
        self.assertEqual(session.current_step, 'enter_svt')

    def test_legacy_alias_still_maps_to_arkesel_json(self):
        response = self.client.post(
            self.url,
            {
                'msisdn': self.phone,
                'text': '*928*013#',
                'sessionId': 'legacy-1',
                'newSession': True,
            },
            format='json',
        )
        data = response.json()
        self.assertTrue(data['continueSession'])
        self.assertIn('INDEX', data['message'].upper())

    def test_voted_lockout_ends_session(self):
        Vote.objects.create(
            user=self.voter,
            election=self.election,
            position=self.position,
            candidate=self.candidate,
            channel=VotingChannel.objects.get(channel_name='ussd'),
            vote_hash='abc',
        )
        USSDSession.objects.create(
            msisdn=self.phone,
            provider_session_id='old',
            user=self.voter,
            election=self.election,
            current_step='done',
            status='completed',
            state_data={'ballot_complete': True},
        )
        response = self._arkesel(sessionID='sess-lock')
        data = response.json()
        self.assertFalse(data['continueSession'])
        self.assertIn('already voted', data['message'].lower())

    def test_closed_election_vote_does_not_block_new_open_election(self):
        """After voting in a closed election, a new open eligible election stays reachable."""
        Vote.objects.create(
            user=self.voter,
            election=self.election,
            position=self.position,
            candidate=self.candidate,
            channel=VotingChannel.objects.get(channel_name='ussd'),
            vote_hash='closed-vote',
        )
        USSDSession.objects.create(
            msisdn=self.phone,
            provider_session_id='old-closed',
            user=self.voter,
            election=self.election,
            current_step='done',
            status='completed',
            state_data={'ballot_complete': True},
        )
        self.election.status = 'closed'
        self.election.save(update_fields=['status'])

        new_election = Election.objects.create(
            title='Next USSD Election',
            status='open',
            allow_ussd_voting=True,
            created_by=self.admin,
        )
        Position.objects.create(
            election=new_election,
            title='Secretary',
            display_order=1,
            is_votable=True,
        )
        VoterEligibility.objects.create(
            election=new_election,
            user=self.voter,
            is_eligible=True,
        )

        response = self._arkesel(sessionID='sess-new-open')
        data = response.json()
        self.assertTrue(data['continueSession'])
        self.assertIn('INDEX', data['message'].upper())
        self.assertNotIn('already voted', data['message'].lower())
