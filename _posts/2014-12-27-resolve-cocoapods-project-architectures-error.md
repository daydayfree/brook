---
layout: post
title: 解决 Cocoapods 编译错误
---

使用 Objective-C 将近2个月了，项目里使用了 Cocoapods 管理第三方类库，虽然知道这个好东西的存在，但是一直没有认真了解过，直到前天遇到一个问题。

```python
ld: symbol(s) not found for architecture x86_64
ld: symbol(s) not found for architecture i386
ld: symbol(s) not found for architecture armv7
```

对于这种没有见过的问题，作为 Baby Developer 只能拷贝整个问题到 Google 上搜答案。

导致这种问题的原因有很多:
1. 实现文件(.m)没有加到 Compile Source 里面
2. Architecture 设置有问题

搜索2天依然没有解决这个问题，最后由同事花一分钟搞定。(掩面哭泣...)

解决方法：
修改编译选项 OTHER_CFLAGS，删除 OTHER_LDFLAGS

```python
OTHER_CFLAGS = (
  "$(inherited)",
  "-DNS_BLOCK_ASSERTIONS=1",
);
```

解决方法非常简单，而且问题原因在 pod install 时候就已经提示我了，我只是将它忽略了，因为它只是警告。
在执行 pod install 时候，如果项目设置有问题，会有类似下面这样的提示：

```python
[!] The `HelloWorld [Debug]` target overrides the `OTHER_CFLAGS` build setting
defined in `Pods/Pods-HelloWorld/Pods-HelloWorld.debug.xcconfig`.
This can lead to problems with the CocoaPods installation
  - Use the `$(inherited)` flag, or
  - Remove the build settings from the target.
```

2天时间给我的教训就是不要忽略警告，而你也应该如此。
