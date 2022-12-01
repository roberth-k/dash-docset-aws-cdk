import unittest
import util


class Tests(unittest.TestCase):
    def test_get_entry_type(self):
        test_cases = [
            ('class CfnCertificate (construct)', 'Resource'),
            ('class JobQueue (construct) 🔹', 'Constructor'),
            ('interface IJobQueue 🔹', 'Interface'),
            ('enum JsonSchemaType', 'Enum'),
            ('aws-cdk-lib.aws_appintegrations module', 'Module'),
            ('interface JobDefinitionProps 🔹', 'Property'),
            ('interface CfnAlertProps', 'Property'),
            ('class CfnAccount (construct)', 'Resource'),
            ('interface GatewayResponseProps', 'Property'),
        ]

        for title, expect in test_cases:
            with self.subTest(title=title):
                actual = util.get_entry_type(title)
                self.assertEqual(actual, expect)
