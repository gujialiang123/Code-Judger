from sandbox_nocgroup import sandbox
import diff
import time

timestamp = lambda: 'J' + time.strftime(r"%Y%m%d_%H%M%S", time.localtime(int(time.time())))
s = sandbox()
s.create(timestamp(), 'python', 'code/sample_1a', 'test/1A')
result = [s.run('python main.py', '{}'.format(i)) for i in range(1, 19)]
print(result)
s.remove()

