from fuse import FUSE

from matrix.client.http_fs import HttpFS


def main(mountpoint: str, url: str):
    FUSE(HttpFS(url), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    # if len(sys.argv) != 3:
    #     print('usage: %s <mountpoint> <url>' % sys.argv[0])
    #     sys.exit(1)
    #
    # main(sys.argv[1], sys.argv[2])
    main("/Users/josephvitko/PycharmProjects/matrix/test/mnt7", "http://localhost:8000")