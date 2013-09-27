---
layout: post
title: 简单正确的方式给 MySQLdb IN 传参
---

MySQLdb 给 IN 传参时候，遇到各种坑，其实默认支持 IN 传参的。

{% highlight ruby %}
id_list = [1, 2, 3]
cursor.execute('SELECT col1, col2 FROM table1 WHERE id IN %s', (id_list,))
{ endhighlight %}

具体可以阅读员外的博客，[猛击这里](http://blog.xupeng.me/2013/09/25/mysqldb-args-processing/)
