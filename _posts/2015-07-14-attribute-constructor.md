--- layout: post title: 定义函数特性之 constructor ---

在C语言里我们可以通过定义函数特性来改变函数的执行方式，比如可以通过 __attribute__((constructor)) 让函数在 main 函数之前执行，还可以通过 constructor 优先级参数区分函数执行的优先级。这样可以在程式真正运行之前做一些额外的检查工作。

+ main 函数执行之前执行 __attribute__((constructor))
+ main 函数执行之后执行 __attribute__((constructor))

```python

#include <stdio.h>
#include <stdlib.h>

static __attribute__((constructor)) void foo()
{
    printf("Hello World\n");
}

static __attribute__((constructor(101))) void foo2()
{
    printf("Welcome\n");
}

static __attribute__((destructor)) void bar()
{
    printf("Bye\n");
}

int main(int args, char **argv)
{
    printf("(__)\n");
    return 0;
}


```

运行的结果：

```python

➜  TestCode  gcc constructor.c -o constructor.a
➜  TestCode  ./constructor.a
Welcome
Hello World
(__)
Bye
➜  TestCode

```

文档链接： https://gcc.gnu.org/onlinedocs/gcc/Function-Attributes.html#Function-Attributes