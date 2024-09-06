import os
import unittest

from src.matrix.common.passthrough.unix import UnixPassthrough
from tests.matrix.common.passthrough.base import BasePassthroughTest


class TestUnixPassthrough(BasePassthroughTest):
    def setUp(self):
        super().setUp()
        self.passthrough = UnixPassthrough()

    def test_chmod(self):
        test_file = os.path.join(self.test_dir, 'test_file')
        open(test_file, 'w').close()

        new_mode = 0o755
        self.passthrough.chmod(test_file, new_mode)

        self.assertEqual(os.stat(test_file).st_mode & 0o777, new_mode)


if __name__ == '__main__':
    unittest.main()