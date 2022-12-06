import sys

import os
import tarfile
import unittest
from typing import Set


class TestAcc(unittest.TestCase):
    _docset: tarfile.TarFile

    @classmethod
    def setUpClass(cls):
        tgz_path = os.environ.get('ACCTEST_TGZ', f'{sys.path[0]}/../.build/latest/AWS-CDK.tgz')
        if not tgz_path:
            raise RuntimeError('Expected environment variable DOCSET_TGZ.')

        cls._docset = tarfile.open(tgz_path, 'r:gz')

    @classmethod
    def tearDownClass(cls):
        cls._docset.close()

    @classmethod
    def read_file(cls, relative_path: str) -> bytes:
        with cls._docset.extractfile(relative_path) as fp:
            return fp.read()

    @classmethod
    def list_files(cls) -> Set[str]:
        return set(cls._docset.getnames())

    def test_sentinel_files(self):
        members = self.list_files()
        self.assertGreater(len(members), 9000)
        self.assertIn('AWS-CDK.docset/icon.png', members)
        self.assertIn('AWS-CDK.docset/Contents/Info.plist', members)
        self.assertIn('AWS-CDK.docset/Contents/Resources/docSet.dsidx', members)
        self.assertIn('AWS-CDK.docset/Contents/Resources/Documents/cdk/api/v2/docs/aws-cdk-lib.aws_apigateway.IRequestValidator.html', members)
