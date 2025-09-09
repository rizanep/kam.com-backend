# # tests/test_email_verification.py
# from django.test import TestCase
# from django.contrib.auth import get_user_model
# from django.urls import reverse
# from rest_framework.test import APITestCase
# from rest_framework import status
# from unittest.mock import patch
# from django.utils import timezone
# from datetime import timedelta
#
# User = get_user_model()
#
#
# class EmailVerificationTestCase(APITestCase):
#     """Test cases for email verification functionality"""
#
#     def setUp(self):
#         """Run before each test method"""
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123',
#             email_verified=False
#         )
#         self.client.force_authenticate(user=self.user)
#
#         # URLs
#         self.send_email_url = reverse('send_email_verification')
#         self.verify_email_url = reverse('verify_email_code')
#
#     def test_send_email_verification_success(self):
#         """Test successful email verification code sending"""
#         with patch('django.core.mail.send_mail') as mock_send_mail:
#             mock_send_mail.return_value = True
#
#             response = self.client.post(self.send_email_url)
#
#             self.assertEqual(response.status_code, status.HTTP_200_OK)
#             self.assertEqual(response.data['message'], 'Verification code sent to your email')
#
#             # Check that user has verification token
#             self.user.refresh_from_db()
#             self.assertIsNotNone(self.user.email_verification_token)
#             self.assertEqual(len(self.user.email_verification_token), 6)
#             self.assertTrue(self.user.email_verification_token.isdigit())
#
#             # Check email was sent
#             mock_send_mail.assert_called_once()
#
#     def test_send_email_already_verified(self):
#         """Test sending code when email is already verified"""
#         self.user.email_verified = True
#         self.user.save()
#
#         response = self.client.post(self.send_email_url)
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data['error'], 'Email is already verified')
#
#     def test_verify_email_code_success(self):
#         """Test successful email verification"""
#         # Generate verification code
#         verification_code = self.user.generate_email_verification_token()
#
#         response = self.client.post(self.verify_email_url, {
#             'code': verification_code
#         })
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data['message'], 'Email verified successfully')
#
#         # Check user is verified
#         self.user.refresh_from_db()
#         self.assertTrue(self.user.email_verified)
#         self.assertEqual(self.user.email_verification_token, '')  # Token cleared
#
#     def test_verify_email_code_invalid_format(self):
#         """Test verification with invalid code format"""
#         test_cases = [
#             {'code': '123', 'expected': 'Invalid verification code format'},  # Too short
#             {'code': '1234567', 'expected': 'Invalid verification code format'},  # Too long
#             {'code': 'abcdef', 'expected': 'Invalid verification code format'},  # Not digits
#             {'code': '', 'expected': 'Verification code is required'},  # Empty
#         ]
#
#         for case in test_cases:
#             response = self.client.post(self.verify_email_url, {'code': case['code']})
#             self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#             self.assertEqual(response.data['error'], case['expected'])
#
#     def test_verify_email_code_wrong_code(self):
#         """Test verification with wrong code"""
#         # Generate a code but use different one
#         self.user.generate_email_verification_token()
#
#         response = self.client.post(self.verify_email_url, {
#             'code': '999999'
#         })
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data['error'], 'Invalid verification code')
#
#     def test_verify_email_code_expired(self):
#         """Test verification with expired code"""
#         # Generate code and manually set it to expired
#         self.user.generate_email_verification_token()
#         self.user.email_verification_expires = timezone.now() - timedelta(minutes=1)
#         self.user.save()
#
#         response = self.client.post(self.verify_email_url, {
#             'code': self.user.email_verification_token
#         })
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data['error'], 'Verification code has expired. Please request a new one.')
#
#     def test_verify_email_no_token_exists(self):
#         """Test verification when no token was generated"""
#         response = self.client.post(self.verify_email_url, {
#             'code': '123456'
#         })
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data['error'], 'No verification code found. Please request a new one.')
#
#     def test_verify_email_already_verified(self):
#         """Test verification when email is already verified"""
#         self.user.email_verified = True
#         self.user.save()
#
#         response = self.client.post(self.verify_email_url, {
#             'code': '123456'
#         })
#
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(response.data['error'], 'Email is already verified')
#
#     @patch('django.core.mail.send_mail')
#     def test_send_email_failure(self, mock_send_mail):
#         """Test email sending failure"""
#         mock_send_mail.side_effect = Exception("SMTP Error")
#
#         response = self.client.post(self.send_email_url)
#
#         self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
#         self.assertEqual(response.data['error'], 'Failed to send verification email. Please try again later.')
#
#     def test_unauthenticated_access(self):
#         """Test that unauthenticated users cannot access verification endpoints"""
#         self.client.force_authenticate(user=None)
#
#         # Test send email
#         response = self.client.post(self.send_email_url)
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#         # Test verify email
#         response = self.client.post(self.verify_email_url, {'code': '123456'})
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#
#
# class UserModelTestCase(TestCase):
#     """Test cases for User model verification methods"""
#
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123'
#         )
#
#     def test_generate_email_verification_token(self):
#         """Test token generation"""
#         token = self.user.generate_email_verification_token()
#
#         # Check token properties
#         self.assertEqual(len(token), 6)
#         self.assertTrue(token.isdigit())
#
#         # Check database fields
#         self.user.refresh_from_db()
#         self.assertEqual(self.user.email_verification_token, token)
#         self.assertIsNotNone(self.user.email_verification_expires)
#
#         # Check expiry is in future
#         self.assertGreater(self.user.email_verification_expires, timezone.now())
#
#     def test_is_email_verification_token_valid(self):
#         """Test token validation method"""
#         # Generate valid token
#         token = self.user.generate_email_verification_token()
#
#         # Test valid token
#         self.assertTrue(self.user.is_email_verification_token_valid(token))
#
#         # Test invalid token
#         self.assertFalse(self.user.is_email_verification_token_valid('999999'))
#
#         # Test expired token
#         self.user.email_verification_expires = timezone.now() - timedelta(minutes=1)
#         self.user.save()
#         self.assertFalse(self.user.is_email_verification_token_valid(token))
#
#     def test_clear_email_verification_token(self):
#         """Test token clearing"""
#         # Generate token first
#         self.user.generate_email_verification_token()
#         self.assertIsNotNone(self.user.email_verification_token)
#
#         # Clear token
#         self.user.clear_email_verification_token()
#
#         # Check token is cleared
#         self.user.refresh_from_db()
#         self.assertEqual(self.user.email_verification_token, '')
#         self.assertIsNone(self.user.email_verification_expires)
#
#
# class EmailVerificationIntegrationTestCase(APITestCase):
#     """Integration tests for complete email verification flow"""
#
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123',
#             email_verified=False
#         )
#         self.client.force_authenticate(user=self.user)
#
#     @patch('django.core.mail.send_mail')
#     def test_complete_verification_flow(self, mock_send_mail):
#         """Test complete verification flow from send to verify"""
#         mock_send_mail.return_value = True
#
#         # Step 1: Send verification code
#         send_response = self.client.post(reverse('send_email_verification'))
#         self.assertEqual(send_response.status_code, status.HTTP_200_OK)
#
#         # Step 2: Get the generated code
#         self.user.refresh_from_db()
#         generated_code = self.user.email_verification_token
#
#         # Step 3: Verify with the code
#         verify_response = self.client.post(reverse('verify_email_code'), {
#             'code': generated_code
#         })
#         self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
#
#         # Step 4: Check final state
#         self.user.refresh_from_db()
#         self.assertTrue(self.user.email_verified)
#         self.assertEqual(self.user.email_verification_token, '')
#
#         # Step 5: Try to send code again (should fail)
#         send_again_response = self.client.post(reverse('send_email_verification'))
#         self.assertEqual(send_again_response.status_code, status.HTTP_400_BAD_REQUEST)
#
#
# # Running Tests Commands:
# """
# # Run all tests
# python manage.py test
#
# # Run specific test file
# python manage.py test tests.test_email_verification
#
# # Run specific test class
# python manage.py test tests.test_email_verification.EmailVerificationTestCase
#
# # Run specific test method
# python manage.py test tests.test_email_verification.EmailVerificationTestCase.test_verify_email_code_success
#
# # Run with verbose output
# python manage.py test --verbosity=2
#
# # Run with coverage (install: pip install coverage)
# coverage run --source='.' manage.py test
# coverage report
# coverage html  # Creates htmlcov/index.html
# """
#
# # Test Configuration in settings.py
# """
# # Add this to your settings.py for testing
# import sys
#
# if 'test' in sys.argv:
#     DATABASES['default'] = {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': ':memory:'
#     }
#
#     # Disable migrations for faster tests
#     class DisableMigrations:
#         def __contains__(self, item):
#             return True
#         def __getitem__(self, item):
#             return None
#
#     MIGRATION_MODULES = DisableMigrations()
#
#     # Use console email backend for tests
#     EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
# """
#
# # Test Best Practices:
# """
# 1. **Test Structure**: Arrange -> Act -> Assert
#    - Arrange: Set up test data
#    - Act: Execute the code being tested
#    - Assert: Check the results
#
# 2. **Test Names**: Should describe what they test
#    - test_verify_email_code_success
#    - test_verify_email_code_invalid_format
#
# 3. **Test Independence**: Each test should be independent
#    - Use setUp() for common setup
#    - Don't rely on test execution order
#
# 4. **Mock External Services**: Don't send real emails in tests
#    - Use @patch decorator
#    - Mock database calls for unit tests
#
# 5. **Test Edge Cases**:
#    - Empty inputs
#    - Invalid formats
#    - Boundary conditions
#    - Error scenarios
#
# 6. **Coverage**: Aim for 80%+ code coverage
#    - Don't obsess over 100%
#    - Focus on critical paths
#
# 7. **Fast Tests**: Tests should run quickly
#    - Use in-memory database
#    - Disable unnecessary features
# """