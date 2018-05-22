---
layout: post
title: Swift 并行编程现状
---

## 现状

截至到现在，Swift 4 并没有提供语言层面上对并行编程的支持，但是我们有 GCD，并且在 Swift 3 中加入了更符合 Swift 语法习惯的形式。

#### 后台队列

要一个操作在后台运行，我们可以通过创建一个后台队列，通过 `async` 来调用传入的 Block 即可：

```
DispatchQueue.global(qos: .background).async {
    // 后台运行的操作
}
```

在 `async` 操作里我们继续派发一些耗时操作，等操作完成之后，将数据同步到 UI 之上：

```
DispatchQueue.global(qos: .background).async {
    // 后台运行的操作

    DispatchQueue.main.async {
        // 更新主界面
    }
}
```

一切看起来很合理流畅，接口简单，代码阅读起来感觉很棒。

#### 调度组

当我们涉及到等多个后台操作一起完成时，再做 UI 之上的操作，就稍微有点复杂了。
我们可能需要定义个 DispatchGroup，执行每个操作时调用 `enter()`，操作完成时调用 `leave()`，最后通过 `notify()` 去执行 UI 操作：

```
let dispatchGroup = DispatchGroup()

dispatchGroup.enter()
DispatchQueue.global().async(group: dispatchGroup, execute: {
    // 后台执行的操作 id=1
    dispatchGroup.leave()
})

dispatchGroup.enter()
DispatchQueue.global().async(group: dispatchGroup, execute: {
    // 后台执行的操作 id=2
    dispatchGroup.leave()
})

...

dispatchGroup.notify(queue: DispatchQueue.main, execute: {
    // 最后更新主界面
})

```

每个后台操作都是并行执行，没有先后顺序，所有的执行结果统一由调度组来执行。
但是某个后台操作依赖另外一个后台操作的结果呢？

#### 操作队列

在 GCD 基础之上，我们可以通过操作队列定义任务的优先级；也可以通过任务依赖，重新定义任务的执行顺序。

```
var queue = OperationQueue()
queue.name = "com.douban.frodo.test"
queue.maxConcurrentOperationCount = 5

queue.addOperation {
    // 后台执行的操作
}

var operation1 = BlockOperation {
    // 后台执行的操作
}

var operation2 = BlockOperation {
    // 后台执行的操作
}

operation1.queuePriority = .veryHigh
operation1.addDependency(operation2)

queue.addOperation(operation1)
queue.addOperation(operation2)
```

除了控制复杂外，操作接口还是非常简洁易读。
实际开发过程中，我们会发现有很多情况是我们在某个操作里，我们需要继续派发新的操作：

```
MovieRequest(id: "1000").send() { movie, error in
    if let movie = movie {
        MovieTrailerRequest(id: movie.trailerID).send() { trailer, error in
            if let trailer = trailer {
                MovieTrailerCommentsRequest(id: trailer.id).send() { comments, error in
                    if let comments = comments {
                        // 更新主界面
                    } else {
                        handleError(error)
                    }
                }
            } else {
                handleError(error)
            }
        }
    } else {
        handleError(error)
    }
}
```

当然你也可以定义多个 Operation，或者定义多个方法，嵌套去调用，但面对简单的 API 调用，好像有点写的不够简洁明了。

## 问题

上面代码里面，我们已经使用最新 Swift 简化闭包的写法，如果使用完整的闭包写法，我们会多出很多 ({ 、})，我们怎样去避免这种丑陋回调？
结合我们 API 返回结果的形式，参考 APIKit 里对闭包返回结果的定义：

```
public enum Result<T, Error: Swift.Error> {
    case success(T)
    case failure(Error)
}
```

上面的嵌套调用就变成了这样：

```
MovieRequest(id: "1000").send() { result in
    switch result:
    case .success(let movie):
        MovieTrailerRequest(id: movie.trailerID).send() { result in
            switch result:
            case .success(let trailer):
                MovieTrailerCommentsRequest(id: trailer.id).send() { result in
                    switch result:
                    case .success(let comments):
                        // 更新主界面
                    case .failure(let error):
                        handleError(error)
                    }
                }
            case .failure(let error):
                handleError(error)
            }
        }
    case .failure(let error):
        handleError(error)
    }
}
```

最大的改变是什么？({}) -> switch...case! 还是丑！

## 解决方案

因为有 Result 对返回结果的包装，导致每一个 API 处理操作都是一致的：成功时派发新操作，失败时处理错误。基于此，如果对 Request 做一层包装，统一处理 API 返回结果，传入闭包分别接收成功或失败的结果即可。
上面 MovieRequest、TrailerRequest、TrailerCommentsRequest 一个链式操作，每个结果都会依赖上一个结果的返回，所以我们需要一个对象用来传递操作。

```
struct Promise<T> {
    init(resolvers: (_ fulfill: @escaping (T) -> Void, _ reject: @escaping (Error) -> Void) -> Void) {
        // 存储 fulfill 和 reject
        // 当 fulfill 被调用时解析为 then；当 reject 被调用时解析为 error
    }

    // 存储的 then 方法，调用者提供的参数闭包将在 fulfill 时调用
    func then<U>(_ body: (T) -> U) -> Promise<U> {
        return Promise<U>{
            //...
        }
    }

    // 调用者提供该方法，参数闭包当 reject 时调用
    func `catch`<Error>(_ body: (Error) -> Void) {
        //...
    }
}

extension Request {
    var promise: Promise<Response> {
        return Promise<Response> { fulfill, reject in
            self.send() { result in
                switch result {
                case .success(let r): fulfill(r)
                case .failure(let e): reject(e)
                }
            }
        }
    }
}
```

Request 成功时调用 `fulfill`, 出错时调用 `reject`。这样每个 Request 可以这样调用：

```
MovieRequest(id: '1000').promise
    .then { movie in
        // TODO
    }.catch { error in
        handleError(error)
    }
```

MovieRequest、TrailerRequest、TrailerCommentsRequest 的链式调用就可以改为：

```
MovieRequest(id: '1000').promise
    .then { movie in
        return TrailerRequest(id: movie.trailerID).promise
    }.then { trailer in
        return TrailerCommentsRequest(id: trailer.id).promise
    }.then { comments in
        // 更新 UI
    }.catch { error in
        handleError(error)
    }
```

代码简洁了很多，老黄会感谢你！

## 参考

1. [APIKit](https://github.com/ishkawa/APIKit)
2. [PromiseKit](https://github.com/mxcl/PromiseKit/)
3. [Swift 中的并发编程(第一部分：现状）](http://swift.gg/2017/09/04/all-about-concurrency-in-swift-1-the-present/)
