import os
import signal
from smtpd import usage

import diff as difflib
import time
import subprocess

class sandbox:
    def create(self, container_name, image_name, code_folder, test_folder, silence=False, reset_before_run=True):
        self.container_name = container_name
        self.image_name = image_name
        self.code_folder = code_folder
        self.silence = silence
        self.reset_before_run = reset_before_run
        self.first_run = True
        self.compiled = False
        self.pid = 0

        if not os.path.isdir(code_folder):
            raise NotADirectoryError(code_folder + " is not a directory")
        if not os.path.isdir(test_folder):
            raise NotADirectoryError(test_folder + " is not a directory")

        if not os.path.exists('run'):
            os.mkdir('run')
        os.chdir('run')

        os.mkdir(container_name)
        os.chdir(container_name)

        self.__log('Info', 'Checking docker and cgroup')
        self.__system(r'docker info > tmp.txt 2>&1')

        with open('tmp.txt', 'r') as f:
            # cgroup version
            pass

        self.__log('Info', 'Creating docker')

        self.__system(
            r'docker run --name {} --cpus=1 -d {} sh -c "trap \"exit\" TERM; while true; do sleep 1; done" > tmp.txt 2>&1'.format(
                container_name, image_name))
        self.docker_created = True

        with open('tmp.txt', 'r') as f:
            self.container_longid = f.readline().strip()

        self.__system(r'rm -f tmp.txt')

        self.__system(r'docker cp ../../{} {}:/code >> log.txt 2>&1'.format(code_folder, container_name))
        self.__system(r'cp -r ../../{} code >> log.txt 2>&1'.format(code_folder))
        self.__system(r'docker cp ../../{} {}:/test >> log.txt 2>&1'.format(test_folder, container_name))
        self.__system(r'cp -r ../../{} test >> log.txt 2>&1'.format(test_folder))
        os.system(r'docker exec -i {} apt-get update >> log.txt 2>&1'.format(container_name))
        os.system(r'docker exec -i {} apt-get install -y time >> log.txt 2>&1'.format(container_name))
        self.status = 'UNKNOWN'

    def compile(self, compile_cmd):
        self.__log('Info', 'Compiling')

        self.status = 'UNKNOWN'
        self.compiled = True

        container_name = self.container_name
        exit_code = self.__system(r'docker exec -w /code {} {} >> log.txt 2>&1'.format(container_name, compile_cmd))
        if exit_code != 0:
            self.__log('Info', 'Compile Error')
            self.status = 'COMPILE ERROR'
            return 1
        return 0

    def extract_cpu_times(self):
        # 读取 time 命令的输出
        get_time_command = f"docker exec {self.container_name} cat time_output.txt"

        time_output = self.__system_out(get_time_command, check_exit_code=True)

        # 提取用户态和系统态 CPU 时间
        user_time = system_time = None
        for line in time_output.split('\n'):
            if 'User time (seconds)' in line:
                user_time = float(line.split(':')[-1].strip())
            elif 'System time (seconds)' in line:
                system_time = float(line.split(':')[-1].strip())

        if user_time is None or system_time is None:
            raise Exception("Failed to parse CPU times from output")

        return int(user_time*1000), int(system_time*1000)

    def extract_memory_usage(self):
        # 读取 time 命令的输出
        get_time_command = f"docker exec {self.container_name} cat time_output.txt"
        time_output = self.__system_out(get_time_command, check_exit_code=True)

        # 提取最大常驻集大小
        max_rss = None
        for line in time_output.split('\n'):
            if 'Maximum resident set size (kbytes)' in line:
                max_rss = int(line.split(':')[-1].strip())

        if max_rss is None:
            raise Exception("Failed to parse memory usage from output")
        return int(max_rss/1024)

    def get_process_cpu_time(self):
        # 使用 docker exec 结合 ps 命令在容器内获取特定 PID 的 CPU 时间
        command = f"docker exec {self.container_name} ps -eo pid,utime,stime | grep '^{self.pid} '"
        result = subprocess.run(command, shell=True, text=True, capture_output=True)

        if result.returncode != 0:
            raise Exception("Failed to get process info")

        # 解析输出，输出格式应为：pid utime stime
        output = result.stdout.strip()
        if not output:
            raise Exception("No such process")

        # 分解输出获取用户态和内核态 CPU 时间
        _, user_time, system_time = output.split()

        # 假设 HZ = 100, 每个 jiffy 是 10 毫秒
        HZ = 100
        user_time_ms = int(user_time) * 1000 / HZ
        system_time_ms = int(system_time) * 1000 / HZ

        # 返回用户态和内核态 CPU 时间（毫秒）
        return user_time_ms, system_time_ms

    def get_memory_usage(self):
        # 使用 ps 命令在容器内获取特定 PID 的内存占用
        command = f"docker exec {self.container_name} ps -eo pid,rss | grep '^{self.pid} '"
        result = subprocess.run(command, shell=True, text=True, capture_output=True)

        if result.returncode != 0:
            raise Exception("Failed to get process memory usage")

        # 解析输出，输出格式应为：pid rss
        output = result.stdout.strip()
        if not output:
            raise Exception("No such process")

        # 分解输出获取内存使用量 (RSS)
        _, rss = output.split()

        # 将 RSS 从 kB 转换为 MB
        memory_usage_mb = int(rss) / 1024

        return memory_usage_mb
    def is_process_running(self):
        """检查指定 PID 的进程是否在 Docker 容器中运行"""

        check_process_command = f"docker exec {self.container_name} ps -q -p {self.pid}"

        stdout, exit_code = self.__system_out2(check_process_command, check_exit_code=False)
        print("fuck:")
        print(self.pid)
        print(exit_code)
        return exit_code == 0  # 如果命令成功执行（找到了进程），返回 True

    def run(self, command, test, time_limit='1000', memory_limit='256',diff=difflib.diff_default ,problem_id = '0'):
        try:
            return self.__run(command, test, time_limit, memory_limit, diff,problem_id)
        except Exception as e:
            if self.docker_created:
                self.__system('docker rm -f {}'.format(self.container_name))
            raise

    def remove(self, delete_testcase=True, delete_code=True):
        container_name = self.container_name
        if delete_testcase:
            self.__system(r"rm -rf test")
        if delete_code:
            self.__system(r"rm -rf code")

        self.__system(r'docker rm -f {} >> log.txt 2>&1'.format(container_name))
        os.chdir('../..')

    def __log(self, level, info):
        if level != 'Debug' and level != 'System' and not self.silence:
            print('[{}] {}'.format(level, info))

        with open('log.txt', 'a') as f:
            f.write('[{}] {}\n'.format(level, info))

    def __system_out2(self, command, check_exit_code=False):
        """执行系统命令，如果需要，检查退出码"""
        import subprocess
        self.__log('System', command)
        result = subprocess.run(command, shell=True, text=True, capture_output=True)

        if check_exit_code and result.returncode != 0:
            raise Exception(f"Command failed with exit code {result.returncode}")

        # 返回标准输出和退出码
        return result.stdout.strip(), result.returncode

    def __system_out(self, command, check_exit_code=False):
        """执行系统命令，如果需要，检查退出码"""
        import subprocess
        self.__log('System', command)
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if check_exit_code and result.returncode != 0:
            raise Exception(f"Command failed with exit code {result.returncode}")
        return result.stdout.strip()

    def __system(self, s, check_exit_code=True):
        self.__log('System', s)
        exit_code = os.system(s)
        if exit_code != 0:
            self.__log('System', 'exit_code = {}'.format(exit_code))
            if check_exit_code:
                raise SystemError('Command Failed : {}'.format(s))
        return exit_code

    def __run(self, command, test, time_limit, memory_limit, diff,problem_id):
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        if self.status == 'COMPILE ERROR':
            return self.status

        container_name = self.container_name

        if self.reset_before_run or (self.compiled and self.first_run):
            self.__log('Info', 'Resetting cgroups')
            self.__system(r'docker restart {} >> log.txt 2>&1'.format(container_name))

        if self.reset_before_run or self.first_run:
            self.__system(
                r'docker update --memory {}m --memory-swap {}m {} >> log.txt 2>&1'.format(memory_limit, memory_limit,
                                                                                        container_name))
            self.first_run = False

        self.timeout = int(time_limit)

        if not os.access(r'test/{}.in'.format(test), os.R_OK):
            raise IOError(r'File {}.in does not exist'.format(test))

        if not os.access(r'test/{}.ans'.format(test), os.R_OK):
            raise FileNotFoundError(r'File {}.ans does not exist'.format(test))

        self.__log('Info', 'Running')
        self.last_real_time = time.time()

        self.fork_pid = os.fork()
        if self.fork_pid == 0:
            docker_command = (
                f"docker exec -i -w /code {container_name} sh -c "
                f"'(/usr/bin/time -v {command} < /test/{test}.in > /test/{test}.out 2> /time_output.txt); echo $! > /tmp/pidfile' 2>> log.txt"
            )
            docker_command = (
                f"docker exec -i -w /code {container_name} sh -c "
                f"'( {command} < /test/{test}.in > /test/{test}.out 2> /command_output.txt & pid=$!; echo $pid > /tmp/pidfile; /usr/bin/time -v -p {command} < /test/{test}.in > /test/{test}.out 2>> /time_output.txt )'"
            )
            # docker_command = (
            #     f"docker exec -i -w /code {container_name} sh -c "
            #     f"'{command} < /test/{test}.in > /test/{test}.out 2> command_output.txt & pid=$!; echo $pid > /tmp/pidfile' 2>> log.txt"
            # )
            exit_code = self.__system(docker_command,
                check_exit_code=False)

            os._exit(0 if exit_code == 0 else 1)
        while 1:
            check_file_command = f"docker exec {container_name} test -f /tmp/pidfile && echo 'exists' || echo 'no'"
            file_exists = self.__system_out(check_file_command, check_exit_code=False)
            if file_exists.strip() == 'exists':
                get_pid_command = f"docker exec {container_name} cat /tmp/pidfile"
                self.pid = self.__system_out(get_pid_command, check_exit_code=True)
                # print("PID:")
                # print(self.pid)
                time.sleep(20000)
                delete_pid_command = f"docker exec {container_name} rm /tmp/pidfile"
                self.__system_out(delete_pid_command, check_exit_code=True)
                break

        self.status = 'UNKNOWN'
        self.running = True
        while self.running:
            # time.sleep(0.1)
            self.__alarm()

        if self.status == 'UNKNOWN':
            self.__system(r'docker cp {}:/test/{}.out test  >> log.txt 2>&1'.format( container_name,test))
            if problem_id == '584A':
                # print("fuck 584A")
                if difflib._584A(r'test/{}.out'.format(test), 'test/{}.ans'.format(test),'test/{}.in'.format(test)):
                    self.status = 'WRONG ANSWER'
                else:
                    self.status = 'ACCEPT'
            else :
                if diff(r'test/{}.out'.format(test), 'test/{}.ans'.format(test)):
                    self.status = 'WRONG ANSWER'
                else:
                    self.status = 'ACCEPT'

        self.__log('Result', self.status + '\n')
        return self.status #, self.time_ms, self.memory_precent

    def __finish(self, status, time_ms, memory_info):
        self.status = status
        self.time_ms = time_ms
        self.memory_precent = memory_info[1]
        #删除time log文件
        delete_time_command = f"docker exec {self.container_name} rm time_output.txt"
        self.__system_out(delete_time_command, check_exit_code=True)
        self.pid = 0

        self.running = False

    def __get_time(self):
        self.__log('Debug', 'get_time')

        if self.is_process_running():
            try:
                user_time, sys_time = self.get_process_cpu_time()
            except:
                user_time, sys_time = self.extract_cpu_times()
        else:
            user_time, sys_time = self.extract_cpu_times()

        sum_cpu_time = user_time+sys_time

        real_time_ms = int((time.time() - self.last_real_time) * 1000)

        self.__log('Limit', 'TimeUsage : used = {}ms  real = {}ms'.format(sum_cpu_time, real_time_ms))
        return sum_cpu_time, real_time_ms

    def __get_memory(self):
        self.__log('Debug', 'get_memory')
        if self.is_process_running():
            try:
                usage = self.get_memory_usage()
            except:
                usage = self.extract_memory_usage()
        else:
            usage = self.extract_memory_usage()
        limit = int(self.memory_limit)

        precent = 100.0 * usage / limit
        self.__log('Limit', 'MemoryUsage : {} / {} = {:.1f}%'.format(usage, limit, precent))
        return precent, usage, limit

    def __alarm(self):
        self.__log('Debug', 'alarm start')
        real = time.time() - self.last_real_time
        if real > 5 * self.timeout + 1000:
            A,B= self.get_process_cpu_time()
            used = A+B
            m = self.__get_memory()
            self.__finish('TIME LIMIT EXECEED', self.time_limit, m)
            os.kill(self.fork_pid, signal.SIGKILL)
            os.wait()
            return

        pid, exit_code = os.waitpid(-1, os.WNOHANG)

        if pid == self.fork_pid:
            self.__log('Debug', 'Exited')
            m = self.__get_memory()
            used,real = self.__get_time()
            if m[0] > 99:
                self.__finish('MEMORY LIMIT EXECEED', used, m)
            elif exit_code != 0:
                self.__finish('RUNTIME ERROR', used, m)
            else:
                self.__finish('UNKNOWN', used, m)

        self.__log('Debug', 'alarm finish')