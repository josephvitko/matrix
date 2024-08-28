import matrix.common.schema.input as fuse_input
import matrix.common.schema.output as fuse_output

from matrix.common import func
from matrix.common.endpoints import FuseEndpoints


endpoint_config = {
    FuseEndpoints.ACCESS.value: {
        'input_type': fuse_input.AccessInput,
        'func': func.access,
        'args': ['path', 'mode'],
        'output_type': None,
    },
    FuseEndpoints.CHMOD.value: {
        'input_type': fuse_input.ChmodInput,
        'func': func.chmod,
        'args': ['path', 'mode'],
        'output_type': None,
    },
    FuseEndpoints.CHOWN.value: {
        'input_type': fuse_input.ChownInput,
        'func': func.chown,
        'args': ['path', 'uid', 'gid'],
        'output_type': None,
    },
    FuseEndpoints.GETATTR.value: {
        'input_type': fuse_input.GetattrInput,
        'func': func.fuse_getattr,
        'args': ['path', 'fh'],
        'output_type': fuse_output.GetattrOutput,
    },
    FuseEndpoints.READDIR.value: {
        'input_type': fuse_input.ReaddirInput,
        'func': func.readdir,
        'args': ['path', 'fh'],
        'output_type': fuse_output.ReaddirOutput,
    },
    FuseEndpoints.READLINK.value: {
        'input_type': fuse_input.ReadlinkInput,
        'func': func.readlink,
        'args': ['path'],
        'output_type': fuse_output.ReadlinkOutput,
    },
    FuseEndpoints.MKNOD.value: {
        'input_type': fuse_input.MknodInput,
        'func': func.mknod,
        'args': ['path', 'mode', 'dev'],
        'output_type': None,
    },
    FuseEndpoints.RMDIR.value: {
        'input_type': fuse_input.RmdirInput,
        'func': func.rmdir,
        'args': ['path'],
        'output_type': None,
    },
    FuseEndpoints.MKDIR.value: {
        'input_type': fuse_input.MkdirInput,
        'func': func.mkdir,
        'args': ['path', 'mode'],
        'output_type': None,
    },
    FuseEndpoints.STATFS.value: {
        'input_type': fuse_input.StatfsInput,
        'func': func.statfs,
        'args': ['path'],
        'output_type': fuse_output.StatfsOutput,
    },
    FuseEndpoints.UNLINK.value: {
        'input_type': fuse_input.UnlinkInput,
        'func': func.unlink,
        'args': ['path'],
        'output_type': None,
    },
    FuseEndpoints.SYMLINK.value: {
        'input_type': fuse_input.SymlinkInput,
        'func': func.symlink,
        'args': ['name', 'target'],
        'output_type': None,
    },
    FuseEndpoints.RENAME.value: {
        'input_type': fuse_input.RenameInput,
        'func': func.rename,
        'args': ['old', 'new'],
        'output_type': None,
    },
    FuseEndpoints.LINK.value: {
        'input_type': fuse_input.LinkInput,
        'func': func.link,
        'args': ['target', 'name'],
        'output_type': None,
    },
    FuseEndpoints.UTIMENS.value: {
        'input_type': fuse_input.UtimensInput,
        'func': func.utimens,
        'args': ['path', 'times'],
        'output_type': None,
    },
    FuseEndpoints.OPEN.value: {
        'input_type': fuse_input.OpenInput,
        'func': func.fuse_open,
        'args': ['path', 'flags'],
        'output_type': fuse_output.OpenOutput,
    },
    FuseEndpoints.CREATE.value: {
        'input_type': fuse_input.CreateInput,
        'func': func.create,
        'args': ['path', 'mode'],
        'output_type': fuse_output.CreateOutput,
    },
    FuseEndpoints.READ.value: {
        'input_type': fuse_input.ReadInput,
        'func': func.read,
        'args': ['path', 'size', 'offset', 'fh'],
        'output_type': fuse_output.ReadOutput,
    },
    FuseEndpoints.WRITE.value: {
        'input_type': fuse_input.WriteInput,
        'func': func.write,
        'args': ['path', 'data', 'offset', 'fh'],
        'output_type': fuse_output.WriteOutput,
    },
    FuseEndpoints.TRUNCATE.value: {
        'input_type': fuse_input.TruncateInput,
        'func': func.truncate,
        'args': ['path', 'length', 'fh'],
        'output_type': None,
    },
    FuseEndpoints.FLUSH.value: {
        'input_type': fuse_input.FlushInput,
        'func': func.flush,
        'args': ['path', 'fh'],
        'output_type': None,
    },
    FuseEndpoints.RELEASE.value: {
        'input_type': fuse_input.ReleaseInput,
        'func': func.release,
        'args': ['path', 'fh'],
        'output_type': None,
    },
    FuseEndpoints.FSYNC.value: {
        'input_type': fuse_input.FsyncInput,
        'func': func.fsync,
        'args': ['path', 'datasync', 'fh'],
        'output_type': None,
    },
}