---
layout: post
title: 通过 Emacs tramp 编辑远程文件
---

我们都知道可以通过 Emacs tramp 来编辑远程文件，可是我在使用 tramp 时候遇到不少的坑，大都是因为没有好好阅读相关的文档，我一般都是某个东西能满足我的需求就行了，所以很少深入的研究某个东西，这是个不好的习惯，得改!

先说说我自己遇到的坑吧。

+ Hangs #1

如果远程服务器使用了 zsh 这样的 shell，tramp 远程连接的时候会导致 Emacs 进程挂起。
{% highlight ruby %}
unsetopt prompt_cr
[[ $TERM == "dumb" ]] && unsetopt zle && PS1='$ '
{% endhighlight %}

+ Hangs #2

编辑虚拟机文件的时候，会遇到域名不能解析的问题。
不知道是不是因为虚拟机的问题，编辑其他服务器文件的时候，没有发现这个问题。后来知道是我写法不规范，但是尼玛为啥编辑其他的就没有问题。不管怎样，正确的方式应该是
{% highlight ruby %}
/ssh:username:hostname:/path/to/file
{% endhighlight %}
如果不写 /path/to/file 编辑虚拟机文件就会出现这个问题。可能是因为我编辑的是 vagrant 里的文件?未知。

+ Mark #1

避免 tramp 每次都输入密码可以将本地 ssh key 保存到远程服务器已认证的用户中。
{% highlight ruby %}
localhost: scp /localhost/.ssh/id_rsa.pub username:hostname:~/
remote: cat ~/id_rsa.pub >> ~/.ssh/authorized_keys
{% endhighlight %}
然后保存到本地 Emacs bookmark 中就行了。

-- EOF --
