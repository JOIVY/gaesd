from contextlib import contextmanager

@contextmanager
class voo(object):
    def __call__(self):
        print 2


if __name__ == '__main__':
    v = voo()

    with v:
        pass

    print 'done'
