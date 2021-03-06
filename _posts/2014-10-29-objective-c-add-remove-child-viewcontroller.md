---
layout: post
title: 给控制器增加子控制器(Objective-C) - addChildViewController
---

在 iOS 开发过程中，有些情况需要从当前控制器弹出新的控制器，来展示页面跳转之外的逻辑。

举个例子：

当所有的试图中都有一个"搜索按钮"时，我们需要随时弹出搜索栏控制器，展示和控制搜索结果等数据。

```python
// BaseViewController.m
SearchViewController *searchVC = [[SearchViewController alloc] init];
[self addChildViewController:searchVC];
searchVC.view.frame = self.view.bounds;
[self.view addSubview:searchVC.view];
[searchVC didMoveToParentViewController:self];
```

点击"取消搜索"按钮时，将 `searchVC` 从当前控制器中去掉。

```python
// SearchViewController.m
[self willMoveToParentViewController:nil];
[self.view removeFromSuperview];
[self removeFromParentViewController];
```

ISSUE: 在 iOS6 or iOS7, 如果 ParentViewController 是 UITabBarViewController 会引起 `ParentViewController Dealloced Error`

可以将移除操作放在 ParentViewContrller 里，ParentViewController 实现移除的代理，设置 SearchViewController 代理为 ParentViewContrller，在取消搜索 Action 中调用代理方法。

苹果官方文档: [猛击这里](https://developer.apple.com/library/ios/featuredarticles/ViewControllerPGforiPhoneOS/CreatingCustomContainerViewControllers/CreatingCustomContainerViewControllers.html)
