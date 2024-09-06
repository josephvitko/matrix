import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from fuse import Operations


class BasePassthroughTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.passthrough: Operations = None

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_mkdir(self):
        new_dir = os.path.join(self.test_dir, 'new_dir')
        mode = 0o755

        self.passthrough.mkdir(new_dir, mode)
        self.assertTrue(os.path.isdir(new_dir))
        self.assertEqual(os.stat(new_dir).st_mode & 0o777, mode)

    def test_create_and_read(self):
        test_file = os.path.join(self.test_dir, 'test_file')
        content = b'Hello, World!'

        # Create file
        mode = 0o644
        self.passthrough.create(test_file, mode)
        self.assertTrue(os.path.exists(test_file))
        self.assertEqual(os.stat(test_file).st_mode & 0o777, mode)

        # Write content
        fh = os.open(test_file, os.O_WRONLY)
        written = self.passthrough.write(test_file, content, 0, fh)
        os.close(fh)
        self.assertEqual(written, len(content))

        # Read content
        fh = os.open(test_file, os.O_RDONLY)
        read_content = self.passthrough.read(test_file, len(content), 0, fh)
        os.close(fh)
        self.assertEqual(read_content, content)

    def test_unlink(self):
        test_file = os.path.join(self.test_dir, 'test_file')
        open(test_file, 'w').close()

        self.passthrough.unlink(test_file)
        self.assertFalse(os.path.exists(test_file))

    def test_rename(self):
        old_path = os.path.join(self.test_dir, 'old_file')
        new_path = os.path.join(self.test_dir, 'new_file')
        open(old_path, 'w').close()

        self.passthrough.rename(old_path, new_path)
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(new_path))

    @patch('os.lstat')
    def test_getattr(self, mock_lstat):
        mock_stat = MagicMock()
        mock_stat.st_mode = 0o644
        mock_stat.st_size = 1024
        mock_lstat.return_value = mock_stat

        attrs = self.passthrough.getattr('/dummy/path')
        self.assertIn('st_mode', attrs)
        self.assertIn('st_size', attrs)
        self.assertEqual(attrs['st_mode'], 0o644)
        self.assertEqual(attrs['st_size'], 1024)
