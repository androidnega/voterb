from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from elections.models import Election, Position, VotingChannel, VoterEligibility
from candidates.models import Candidate
from system.models import SystemSetting, FeatureFlag
from ussd.models import USSDSession, USSDRequestLog
from voting.models import Vote


class USSDWebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        SystemSetting.objects.update_or_create(
            key='ussd_enabled',
            defaults={'value': 'true', 'category': 'integrations'},
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

    def test_welcome_asks_for_index(self):
        response = self.client.post(
            self.url,
            {'msisdn': self.phone, 'text': '*920#', 'sessionId': 'sess-1', 'newSession': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertTrue(body.startswith('CON '))
        self.assertIn('INDEX', body.upper())
        self.assertEqual(USSDSession.objects.count(), 1)
        self.assertEqual(USSDRequestLog.objects.count(), 1)

    def test_arkesel_alias_payload_for_live_short_code(self):
        SystemSetting.objects.update_or_create(
            key='ussd_service_code',
            defaults={'value': '*928*013#', 'category': 'integrations'},
        )
        response = self.client.post(
            self.url,
            {
                'msisdn': self.phone,
                'userData': '*928*013#',
                'sessionID': 'arkesel-sess-1',
                'newSession': 'true',
                'userID': 'R3ETNHCMVR_LOHp',
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertTrue(body.startswith('CON '))
        self.assertIn('INDEX', body.upper())
        session = USSDSession.objects.get(provider_session_id='arkesel-sess-1')
        self.assertEqual(session.msisdn, self.phone)
        self.assertEqual(session.current_step, 'enter_index')

    def test_index_issues_svt_prompt(self):
        sid = 'sess-svt'
        self.client.post(
            self.url,
            {'msisdn': self.phone, 'text': '*920#', 'sessionId': sid, 'newSession': True},
            format='json',
        )
        r2 = self.client.post(
            self.url,
            {'msisdn': self.phone, 'text': f'*920*{self.index}', 'sessionId': sid},
            format='json',
        )
        body = r2.content.decode()
        self.assertTrue(body.startswith('CON '))
        self.assertIn('SVT', body.upper())
        session = USSDSession.objects.filter(provider_session_id=sid).first()
        self.assertEqual(session.current_step, 'enter_svt')

    def test_voted_lockout_without_index(self):
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
        response = self.client.post(
            self.url,
            {'msisdn': self.phone, 'text': '*920#', 'sessionId': 'sess-lock', 'newSession': True},
            format='json',
        )
        body = response.content.decode()
        self.assertTrue(body.startswith('END '))
        self.assertIn('already voted', body.lower())
