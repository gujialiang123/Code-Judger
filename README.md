###   一个本地的基于docker的评测器，可以自动对代码进行评测

##### 说明： 

需要docker，需要安装docker并提前使用pull拉取镜像到本地。

目前支持python，c++

如果使用python，请提前docker pull python

如果使用pypy，请提前docker pull pypy

如果想要评测c++代码，请提前docker pull gcc

sandbox_docker_api是可以在所有环境下运行的版本，但是效率较低。

sandbox需要在运行cgroup1的linux系统下运行，速度较快

使用说明：

例子如下：
```python
s = sandbox()
    s.create(timestamp(), 'python', 'code/plus-std', 'testcase/plus', silence=True, reset_before_run=True)
    # s.compile()
    result = [s.run('python main.py', '{}'.format(i)) for i in range(1, 4)]
    print(result)
    s.remove()

    s = sandbox()
    s.create(timestamp(), 'gcc', 'code/plus-cpp-std', 'testcase/plus', silence=True, reset_before_run=True)
    s.compile('g++ main.cpp -o main')
    result = [s.run('./main', '{}'.format(i)) for i in range(1, 4)]
    print(result)
    s.remove()

```
请使用s = sandbox() 创建对应的对象

s.create是用于创建对应的docker使用的，第一个参数可以随便改，只要保证不会出现同名的docker就可以，这里默认使用时间戳。第二个参数是使用什么docker镜像，python请使用python，c++请使用gcc，pypy请使用pypy，其他语言可以使用自己需要的镜像。

s.create函数的第三个第四个参数分别指定代码的路径和测试用例的路径，具体格式可以参考例子。

silence参数表示是否在命令行输出结果。

reset_before_run表示是否在每次评测后重置cgroup，True会提高结果准确率但是降低评测速度

仅对cgroup的版本有效，如果是dockerapi的版本请设置为false以提高效率（

如果是c++等需要编译的语言，需要使用s.compile指令。评测命令可以自定义，例如o2 o3等等

s.run用于运行代码，格式可以参考judge.py，返回的三个结果分别是评测结果，运行时间和内存占用。

最后记得使用s.remove删除docker

如果需要special judge，请在diff中设置spj的函数

