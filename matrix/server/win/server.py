import base64
import os
import threading

import pywintypes
import win32con
import win32file

from flask import Flask, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest

from matrix.common.endpoints import FuseEndpoints

app = Flask(__name__)

open_files = {}
open_files_lock = threading.Lock()

# Retrieve the root from the environment variable or set to a default value
ROOT = os.getenv('FS_ROOT', 'C:\\tmp\\test-root')


def full_path(partial):
    if partial.startswith("/"):
        partial = partial[1:]
    return os.path.join(ROOT, partial)


def lock_file(fh):
    """
    Locks the entire file using the Windows LockFile API.
    fh: File handle obtained from os.open()
    """
    overlapped = pywintypes.OVERLAPPED()
    win32file.LockFileEx(fh, win32con.LOCKFILE_EXCLUSIVE_LOCK, 0, -0x10000, overlapped)


def unlock_file(fh):
    """
    Unlocks the file using Windows UnlockFile API.
    fh: File handle obtained from os.open()
    """
    overlapped = pywintypes.OVERLAPPED()
    win32file.UnlockFileEx(fh, 0, -0x10000, overlapped)


@app.route(FuseEndpoints.ACCESS.value, methods=['POST'])
def access():
    data = request.json
    path = full_path(data['path'])
    mode = data['mode']
    print(f"Checking access to {path} with mode {mode}")
    if not os.access(path, mode):
        raise BadRequest(description="Permission denied")
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.CHMOD.value, methods=['POST'])
def chmod():
    data = request.json
    path = full_path(data['path'])
    mode = data['mode']
    print(f"Changing mode of {path} to {mode}")
    os.chmod(path, mode)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.CHOWN.value, methods=['POST'])
def chown():
    data = request.json
    path = full_path(data['path'])
    uid = data['uid']
    gid = data['gid']
    print(f"Changing owner of {path} to {uid}:{gid}")
    os.chown(path, uid, gid)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.GETATTR.value, methods=['POST'])
def getattr_rout():
    data = request.json
    path = full_path(data['path'])
    print(f"Getting attributes of {path}")
    stat = os.lstat(path)
    result = {key: getattr(stat, key) for key in ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid')}
    return jsonify(result)


@app.route(FuseEndpoints.READDIR.value, methods=['POST'])
def readdir():
    data = request.json
    path = full_path(data['path'])
    print(f"Reading directory {path}")
    dirents = ['.', '..'] + os.listdir(path)
    return jsonify({"content": dirents})


@app.route(FuseEndpoints.READLINK.value, methods=['POST'])
def readlink():
    data = request.json
    path = full_path(data['path'])
    print(f"Reading link {path}")
    target = os.readlink(path)
    return jsonify({"path": target})


@app.route(FuseEndpoints.MKNOD.value, methods=['POST'])
def mknod():
    data = request.json
    path = full_path(data['path'])
    mode = data['mode']
    dev = data['dev']
    print(f"Creating node {path} with mode {mode} and dev {dev}")
    os.mknod(path, mode, dev)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.RMDIR.value, methods=['POST'])
def rmdir():
    data = request.json
    path = full_path(data['path'])
    print(f"Removing directory {path}")
    os.rmdir(path)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.MKDIR.value, methods=['POST'])
def mkdir():
    data = request.json
    path = full_path(data['path'])
    mode = data['mode']
    print(f"Creating directory {path} with mode {mode}")
    os.mkdir(path, mode)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.STATFS.value, methods=['POST'])
def statfs():
    data = request.json
    path = full_path(data['path'])

    print(f"Getting filesystem stats for {path}")

    if not os.path.exists(path):
        raise NotFound(description="Path does not exist")

    sectors_per_cluster, bytes_per_sector, num_free_clusters, total_num_clusters = \
        win32file.GetDiskFreeSpace(path)
    total_size = total_num_clusters * sectors_per_cluster * bytes_per_sector
    free_size = num_free_clusters * sectors_per_cluster * bytes_per_sector

    return jsonify({
        'f_bsize': bytes_per_sector,
        'f_frsize': bytes_per_sector,
        'f_blocks': total_num_clusters,
        'f_bfree': num_free_clusters,
        'f_bavail': num_free_clusters,  # Usually the same on Windows
        'f_files': 0,  # Not directly available
        'f_ffree': 0,  # Not directly available
        'f_namemax': 255,  # Typical for NTFS and FAT
    })


@app.route(FuseEndpoints.UNLINK.value, methods=['POST'])
def unlink():
    data = request.json
    path = full_path(data['path'])
    print(f"Unlinking {path}")
    os.unlink(path)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.SYMLINK.value, methods=['POST'])
def symlink():
    data = request.json
    target = full_path(data['target'])
    name = data['name']
    print(f"Creating symlink {name} -> {target}")
    os.symlink(target, name)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.RENAME.value, methods=['POST'])
def rename():
    data = request.json
    old = full_path(data['old'])
    new = full_path(data['new'])
    print(f"Renaming {old} to {new}")
    os.rename(old, new)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.LINK.value, methods=['POST'])
def link():
    data = request.json
    target = full_path(data['target'])
    name = data['name']
    print(f"Creating hard link {name} -> {target}")
    os.link(target, name)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.UTIMENS.value, methods=['POST'])
def utimens():
    data = request.json
    path = full_path(data['path'])
    times = data['times']
    print(f"Setting times of {path} to {times}")
    os.utime(path, times)
    return jsonify({"status": "success"})


@app.route(FuseEndpoints.OPEN.value, methods=['POST'])
def open_file():
    data = request.json
    path = full_path(data['path'])
    flags = data['flags']
    access = win32con.GENERIC_READ if flags & os.O_RDONLY else win32con.GENERIC_WRITE
    print(f"Opening file {path} with flags {flags}")
    try:
        # Open file and create a Windows file handle
        fh = win32file.CreateFile(
            path,
            access,
            win32con.FILE_SHARE_READ,  # Adjust sharing mode as needed
            None,
            win32con.OPEN_EXISTING,
            0,
            None
        )
        # Try to lock the file
        lock_file(fh)
        print(f"Opened file {path} with handle {fh.handle}")
        return jsonify({"handle": fh.handle}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(FuseEndpoints.CREATE.value, methods=['POST'])
def create_file():
    data = request.json
    path = full_path(data['path'])
    mode = data.get('mode', 0o666)  # Default file mode
    buf = data.get('buf', '')  # Optional Base64 encoded initial data

    # Convert mode from octal to win32file constants
    access = win32con.GENERIC_READ | win32con.GENERIC_WRITE
    share_mode = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE
    security_attrs = None
    creation_disposition = win32con.CREATE_ALWAYS  # Overwrites if exists or creates new
    flags_and_attributes = win32con.FILE_ATTRIBUTE_NORMAL
    template_file = None

    try:
        # Create or open file
        fh = win32file.CreateFile(
            path,
            access,
            share_mode,
            security_attrs,
            creation_disposition,
            flags_and_attributes,
            template_file
        )

        if buf:  # If there is initial data to write
            binary_data = base64.b64decode(buf)
            win32file.WriteFile(fh, binary_data)

        handle = fh.handle
        win32file.CloseHandle(fh)  # Close the file handle after writing initial data
        return jsonify({"status": "success", "handle": handle}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def read_file_as_base64(path):
    """
    Read file from the given path and encode its content to Base64.
    This function assumes that the file might contain binary data.
    """
    with open(path, 'rb') as file:
        binary_data = file.read()
    return base64.b64encode(binary_data).decode('ascii')


@app.route(FuseEndpoints.READ.value, methods=['POST'])
def read_file():
    data = request.json
    path = full_path(data['path'])
    size = data['length']
    offset = data['offset']
    try:
        fh = win32file.CreateFile(
            path,
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ,
            None,
            win32con.OPEN_EXISTING,
            0,
            None
        )
        win32file.SetFilePointer(fh, offset, win32con.FILE_BEGIN)
        (hr, data) = win32file.ReadFile(fh, size)
        win32file.CloseHandle(fh)
        return jsonify({"data": base64.b64encode(data).decode('ascii')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(FuseEndpoints.WRITE.value, methods=['POST'])
def write_file():
    data = request.json
    handle = data['fh']
    buf = data['buf']  # Expecting Base64-encoded string
    offset = data['offset']
    try:
        fh = win32file._get_osfhandle(int(handle))
        win32file.SetFilePointer(fh, offset, win32con.FILE_BEGIN)
        # Decode the Base64 encoded string back to binary
        binary_data = base64.b64decode(buf)
        (hr, bytes_written) = win32file.WriteFile(fh, binary_data)
        return jsonify({"written": bytes_written}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(FuseEndpoints.TRUNCATE.value, methods=['POST'])
def truncate_file():
    data = request.json
    path = full_path(data['path'])
    length = data['length']  # Length to truncate to

    # Open file with generic write access
    try:
        fh = win32file.CreateFile(
            path,
            win32con.GENERIC_WRITE,
            0,  # No sharing mode
            None,  # No security attributes
            win32con.OPEN_EXISTING,  # Opens the file if it exists
            0,  # No special attributes
            None  # No template file
        )

        # Set the file pointer to the truncate length
        win32file.SetFilePointer(fh, length, win32con.FILE_BEGIN)

        # Set the end of the file to the current position
        win32file.SetEndOfFile(fh)

        # Close the file handle
        win32file.CloseHandle(fh)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(FuseEndpoints.FLUSH.value, methods=['POST'])
def flush_file():
    data = request.json
    handle = data['fh']  # This should be the file handle

    try:
        fh = win32file._get_osfhandle(int(handle))

        # Flush the file buffers to disk
        win32file.FlushFileBuffers(fh)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(FuseEndpoints.RELEASE.value, methods=['POST'])
def close_file():
    data = request.json
    handle = data['fh']
    print(f"Releasing file with handle {handle}")
    try:
        fh = win32file._get_osfhandle(handle)
        unlock_file(fh)
        win32file.CloseHandle(fh)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(FuseEndpoints.FSYNC.value, methods=['POST'])
def fsync_file():
    data = request.json
    handle = data['fh']  # This should be the file handle as stored/retrieved in previous operations
    fdatasync = data.get('fdatasync', False)  # Optional, if only flushing data, not metadata

    try:
        fh = win32file._get_osfhandle(int(handle))

        # Flush the file buffers to disk, including metadata unless fdatasync is specifically true
        win32file.FlushFileBuffers(fh)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
