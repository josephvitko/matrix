import os
import shutil
import time
import unittest

import win32con
import win32file
import win32security
import ntsecuritycon as con

from src.matrix.common.passthrough.nt import WindowsNTPassthrough
from tests.matrix.common.passthrough.base import BasePassthroughTest


class TestWindowsNTPassthrough(BasePassthroughTest):
    def setUp(self):
        super().setUp()
        self.passthrough = WindowsNTPassthrough(self.test_dir)

    def tearDown(self):
        del self.passthrough
        time.sleep(0.1)  # Give some time for file handles to be released
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_and_read(self):
        test_file = os.path.join(self.test_dir, 'test_file')
        content = b'Hello, World!'

        # Create file
        fh = self.passthrough.create(test_file, 0o644)
        self.assertTrue(os.path.exists(test_file))

        # Write content
        written = self.passthrough.write(test_file, content, 0, fh)
        self.assertEqual(written, len(content))
        self.passthrough.release(test_file, fh)

        # Read content
        fh = self.passthrough.open(test_file, os.O_RDONLY)
        read_content = self.passthrough.read(test_file, len(content), 0, fh)
        self.passthrough.release(test_file, fh)
        self.assertEqual(read_content, content)

    def test_mkdir(self):
        new_dir = os.path.join(self.test_dir, 'new_dir')
        mode = 0o755

        self.passthrough.mkdir(new_dir, mode)
        self.assertTrue(os.path.isdir(new_dir))

        # Check Windows-specific permissions
        security_descriptor = win32security.GetFileSecurity(new_dir, win32security.DACL_SECURITY_INFORMATION)
        dacl = security_descriptor.GetSecurityDescriptorDacl()

        # Get the SID for the current user
        user_sid = win32security.GetFileSecurity(new_dir,
                                                 win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()

        # Check if the user has full control
        for i in range(dacl.GetAceCount()):
            ace = dacl.GetAce(i)
            if ace[2] == user_sid and ace[1] == con.FILE_ALL_ACCESS:
                break
        else:
            self.fail("User does not have full control over the created directory")

    @unittest.skipIf(os.name != 'nt', "Windows-specific test")
    def test_case_insensitive_file_names(self):
        test_file = os.path.join(self.test_dir, 'TestFile.txt')
        self.passthrough.create(test_file, 0o644)
        self.assertTrue(os.path.exists(test_file.lower()))

    @unittest.skipIf(os.name != 'nt', "Windows-specific test")
    def test_alternative_data_streams(self):
        test_file = os.path.join(self.test_dir, 'ads_test.txt')
        main_content = b'Main content'
        ads_content = b'ADS content'
        ads_name = 'ads_test'

        # Write and read main stream
        fh = self.passthrough.create(test_file, 0o644)
        written = self.passthrough.write(test_file, main_content, 0, fh)
        self.assertEqual(written, len(main_content))
        self.passthrough.release(test_file, fh)

        fh = self.passthrough.open(test_file, os.O_RDONLY)
        read_content = self.passthrough.read(test_file, len(main_content), 0, fh)
        self.passthrough.release(test_file, fh)
        self.assertEqual(read_content, main_content)

        # Write and read alternative data stream
        ads_path = f"{test_file}:{ads_name}"
        fh = self.passthrough.create(ads_path, 0o644)
        written = self.passthrough.write(ads_path, ads_content, 0, fh)
        self.assertEqual(written, len(ads_content))
        self.passthrough.release(ads_path, fh)

        fh = self.passthrough.open(ads_path, os.O_RDONLY)
        read_ads_content = self.passthrough.read(ads_path, len(ads_content), 0, fh)
        self.passthrough.release(ads_path, fh)
        self.assertEqual(read_ads_content, ads_content)

        # Write and read main stream
        fh = self.passthrough.create(test_file, 0o644)
        self.passthrough.write(test_file, main_content, 0, fh)
        self.passthrough.release(test_file, fh)

        fh = self.passthrough.open(test_file, os.O_RDONLY)
        read_content = self.passthrough.read(test_file, len(main_content), 0, fh)
        self.passthrough.release(test_file, fh)
        self.assertEqual(read_content, main_content)

        # Write and read alternative data stream
        ads_path = f"{test_file}:{ads_name}"
        fh = self.passthrough.open(ads_path, os.O_WRONLY | os.O_CREAT)
        self.passthrough.write(ads_path, ads_content, 0, fh)
        self.passthrough.release(ads_path, fh)

        fh = self.passthrough.open(ads_path, os.O_RDONLY)
        read_ads_content = self.passthrough.read(ads_path, len(ads_content), 0, fh)
        self.passthrough.release(ads_path, fh)
        self.assertEqual(read_ads_content, ads_content)

    @unittest.skipIf(os.name != 'nt', "Windows-specific test")
    def test_long_file_names(self):
        long_name = 'a' * 250 + '.txt'  # 254 characters total
        long_path = os.path.join(self.test_dir, long_name)
        self.passthrough.create(long_path, 0o644)
        self.assertTrue(os.path.exists(long_path))

    @unittest.skipIf(os.name != 'nt', "Windows-specific test")
    def test_file_attributes(self):
        hidden_file = os.path.join(self.test_dir, 'hidden.txt')
        self.passthrough.create(hidden_file, 0o644)
        win32file.SetFileAttributes(hidden_file, win32con.FILE_ATTRIBUTE_HIDDEN)

        attrs = win32file.GetFileAttributes(hidden_file)
        self.assertTrue(attrs & win32con.FILE_ATTRIBUTE_HIDDEN)

    @unittest.skipIf(os.name != 'nt', "Windows-specific test")
    def test_reserved_names(self):
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                          'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                          'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

        for name in reserved_names:
            with self.assertRaises(OSError):
                self.passthrough.create(os.path.join(self.test_dir, name), 0o644)

    @unittest.skipIf(os.name != 'nt', "Windows-specific test")
    def test_file_times(self):
        test_file = os.path.join(self.test_dir, 'time_test.txt')
        fh = self.passthrough.create(test_file, 0o644)
        self.passthrough.release(test_file, fh)

        # Set creation, modification, and access times
        current_time = int(time.time())
        access_time = current_time - 3600  # 1 hour ago
        mod_time = current_time - 1800  # 30 minutes ago

        # Use our utimens method to set the times
        self.passthrough.utimens(test_file, (access_time, mod_time))

        # Get file times
        handle = win32file.CreateFile(
            test_file, win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
            None, win32file.OPEN_EXISTING, 0, None
        )
        try:
            ctime, atime, mtime = win32file.GetFileTime(handle)
        finally:
            win32file.CloseHandle(handle)

        # Convert to Unix timestamp and check
        self.assertAlmostEqual(atime.timestamp(), access_time, delta=1)
        self.assertAlmostEqual(mtime.timestamp(), mod_time, delta=1)


if __name__ == '__main__':
    unittest.main()
