def diff_default(file1, file2):
    def trans(s):
        s = list(map(lambda s: s.rstrip(), s.split('\n')))
        if s[-1] == '':
            s = s[:-1]
        return s

    with open(file1) as f:
        f1 = trans(f.read())
    with open(file2) as f:
        f2 = trans(f.read())

    return f1 != f2


def _584A(file1, file2, file3):
    def trans(s):
        s = list(map(lambda s: s.rstrip(), s.split('\n')))
        if s[-1] == '':
            s = s[:-1]
        return s

    with open(file1) as f:
        f1 = trans(f.read())
    with open(file2) as f:
        f2 = trans(f.read())
    if not len(f1) == 1:
        return True
    f1 = f1[0]
    f2 = f2[0]
    if int(f2) == -1:
        return f1 != f2

    with open(file3) as f:
        line = f.readline()
        n, t = map(int, line.split())

    if not f1.isdigit():
        return True
    if len(f1) != n:
        return True

    if f1[0] == '0':
        return True

    s1 = int(f1)
    if s1 % t == 0:
        return False
    else:
        return True