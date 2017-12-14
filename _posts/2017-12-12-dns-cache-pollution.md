---
layout: post
title: DNS Cache Pollution
---

## 域名服务器缓存污染

域名服务器缓存污染（DNS cache pollution），又称域名服务器缓存投毒（DNS cache poisoning），
是指一些刻意制造或无意中制造出来的域名服务器封包，把域名指往不正确的IP地址。

一般来说，在互联网上都有可信赖的域名服务器，但为减低网络上的流量压力，一般域名
服务器都会把从上游的域名服务器获得的解析记录暂存起来，待下次有其他机器要求解析
域名时，可以立即提供服务。一旦有关域名的局域域名服务器的缓存受到污染，就会把域
名内的电脑导引往错误的服务器或服务器的网址。

域名服务器缓存污染可能是因为域名服务器软件的设计错误而产生，但亦可能由别有用心
者透过研究开放架构的域名服务器系统来利用当中的漏洞。

## 缓存污染的危害

由于目标真实 IP 地址不正确，可能导致我们的网络请求没有响应；在正常浏览的网页里
面插入一些奇怪的广告；跳转到钓鱼网站；一方面会消耗我们的流量，另一方面可能会对
我们个人信息安全造成隐患。

排除因为域名服务器软件设计的问题，导致缓存污染的主要原因有：

1. 第三方恶意攻击，劫持网络运营商域名过程，嵌入自己的内容。
2. 运行商作怪，允许第三方在自己的链接里嵌入第三方内容。

(举例)

## 怎样避免缓存污染带来的危害

不使用域名解析服务。

## HTTPDNS 技术实现

由于域名到 IP 逻辑比较简单，现在阿里云、七牛云、腾讯云都有成熟的技术解决方案。
用户通过 HTTP 直接访问云服务器，获取对应域名的 IP 地址列表，用户拿到 IP 地址之
后，替换掉请求链接中的域名，通过 IP 直连的方式请求目标服务器，中间不经过域名解
析服务器。

云服务器返回 IP 地址的同时，会返回 IP TTL，用户可以在 TTL 范围内将结果缓存，避
免额外请求的同时，让响应更加及时。

### iOS 客户端技术实现

客户端通过 `NSURLProtocol` 截获所有从本地终端发出的 HTTP/HTTPS 请求 (除
WKWebView 里面的 POST 请求)，替换域名为 IP，再通过 `NSURLSession` 创建一个新的
请求发出。

### 基于 HTTPS 实现原理

替换 HOST 为 IP 地址后，通过 NSURLSession 创建连接到服务器，需要验证 HTTPS 证书的合法性，
所以发送 Request 之前需要将 HOST 值设置到 Request Header 里面，验证时通过 Request Header
里面的 HOST 校验证书的合法性。

下面是一个 IP 只对应一个 HOST 的情况。

```
- (void)URLSession:(NSURLSession *)session
              task:(NSURLSessionTask *)task
didReceiveChallenge:(NSURLAuthenticationChallenge *)challenge
 completionHandler:(void (^)(NSURLSessionAuthChallengeDisposition disposition, NSURLCredential *_Nullable credential))completionHandler
{
  if (self.client != nil && self.dataTask == task) {
    NSURLSessionAuthChallengeDisposition disposition = NSURLSessionAuthChallengePerformDefaultHandling;
    NSURLCredential *credential = nil;

    if ([[[challenge protectionSpace] authenticationMethod] isEqualToString:NSURLAuthenticationMethodServerTrust]) {
      SecTrustRef serverTrust = [[challenge protectionSpace] serverTrust];

      if (serverTrust != NULL) {
        SecPolicyRef policy = NULL;

        NSString *host = [[[self dataTask] originalRequest] valueForHTTPHeaderField:@"Host"];
        if (host == nil || [host length] == 0) {
          host = [[challenge protectionSpace] host];
        }

        if (host != nil && [host length] > 0) {
          policy = SecPolicyCreateSSL(true, (__bridge CFStringRef)host);
        }

        if (policy == NULL) {
          policy = SecPolicyCreateBasicX509();
        }

        SecTrustSetPolicies(serverTrust, policy);
        CFRelease(policy);

        SecTrustResultType result = kSecTrustResultInvalid;
        if (SecTrustEvaluate(serverTrust, &result) == noErr &&
            (result == kSecTrustResultProceed || result == kSecTrustResultUnspecified)) {
          disposition = NSURLSessionAuthChallengeUseCredential;
          credential = [NSURLCredential credentialForTrust:serverTrust];
        } else {
          disposition = NSURLSessionAuthChallengeCancelAuthenticationChallenge;
        }
      }
    }

    completionHandler(disposition, credential);
  }
}

```

如果一个 IP 对应多个 HOST，怎样确保服务端下发正确的证书？

解决方案就是 SNI。

发送 HTTPS 请求首先要进行 SSL/TLS 握手，握手过程是：

1. 客户端发起握手请求，携带随机数，支持的算法列表等参数；
2. 服务端收到请求，选择合适的算法，下发公钥证书和随机数；
3. 客户端对服务端证书进行校验，并发送随机数，该信息使用公钥加密；
4. 服务端通过私钥获取随机数信息；
5. 双方根据以上交互的信息生成 Session Ticket，用作该连接后续数据传输的加密密钥；

握手过程中与 HTTPDNS 有关的是第 3 步，客户端需要验证服务端下发的证书，验证过程有：

1. 客户端用本地保存的根证书解开证书链，确认服务器下发的证书是由可信任的结构颁发；
2. 客户端需要检验证书的 domain 域和扩展域，看是否包含本次请求的 host;

客户端验证过程中第 2 步，由于 host 被 ip 替换，导致 domain 验证不匹配，最终导致
SSL/TLS 握手不成功，当前链接被中断


#### 服务器证书下发

服务器证书与域名关联，一个服务器可能包含多个域名服务(比如图片CDN)，服务器需要根
据客户端发送的 host name 来下发对应的证书。

为了解决这种问题，出现了 SNI (Server Name Indication)。工作原理是：

1. 在连接服务器建立 SSL 链接之前发送要访问站点的域名。
2. 服务器根据域名下发一个合适的证书。

如果获取不到 HOST 信息，服务器会下发一个通用证书，或者是一个错误的证书。

#### 如何为 SSL 连接设置请求的域名

NSURLConnection / NSURLSession 都没有提供接口进行 SNI 域名配置，需要使用
Socket 底层的网络库，例如 CFNetwork。

基于 CFNetwork 的解决方案需要开发者考虑数据的收发、重定向、解码、缓存等问题，
自己实现比较复杂，但是有偷懒的做法，目前我们用的就是偷懒的做法。


#### 通过 CFNetwork 实现过程

+ 为创建 SSL Session 做准备

    - 创建一个 SSLConnection *创建方法后续再讲*。

    - 通过 `SSLCreateContext` 创建一个 SSL Session Context。

        `SSLContextRef SSLCreateContext(CFAllocatorRef alloc, SSLProtocolSide protocolSide, SSLConnectionType connectionType);`

    - 通过 `SSLSetIOFuncs` 设置 SSL Session IO 方法。

        `OSStatus SSLSetIOFuncs(SSLContextRef context, SSLReadFunc readFunc, SSLWriteFunc writeFunc);`

    - 通过 `SSLSetConnection` 指定 SSL Connection。

        `OSStatus SSLSetConnection(SSLContextRef context, SSLConnectionRef connection);`

    - 通过 `SSLSetPeerDomainName` 设置与服务端握手时下发证书的凭证。

        `OSStatus SSLSetPeerDomainName(SSLContextRef context, const char *peerName, size_t peerNameLen);`

+ 创建 SSL Session

    - 通过 `SSLHandshake` 实现与服务端握手。

+ 使用 SSL Session

    - 使用 `SSLRead` `SSLWrite` 来收发数据。

后续创建 HTTP Connection 收发数据，通过 HTTP Response Status 来缓存数据。

#### 如何创建一个 SSLConnectionRef 对象

在创建 SSL Session 之前，客户端必须确保 Connection 对象已经创建好。我们可以通过 CFNetwork, BSD Sockets, 或者其他的开发协议创建一个。

```
// FRDSecureTransportConnection.h

static OSStatus FRDSSLRead(SSLConnectionRef inConnection, void *data, size_t *dataLength);
static OSStatus FRDSSLWrite(SSLConnectionRef connection, const void *data, size_t *dataLength);

@interface FRDSecureTransportConnection ()

@property (nonatomic, strong) NSMutableData *buffer;

@end

@implementation FRDSecureTransportConnection

- (BOOL)connect
{
  OSStatus theStatus = SSLGetSessionState(self.context, &theState);

  if (theState == kSSLIdle || theState == kSSLHandshake) {
    theStatus = SSLHandshake(self.context);

    if (theStatus == noErr || theStatus == errSSLWouldBlock) {
      return YES;
    }
  }

  return NO;
}

- (void)sendData:(NSData *)data
{
  // TODO: Create a stream.
}

- (void)getData:(NSData *)data
{
  SSLSessionState theStatus = SSLRead(self.context, [data mutableBytes], theBufferLength, &theProcessedLength);
  // TODO: Save the data.
}

@end


static OSStatus FRDSSLRead(SSLConnectionRef inConnection, void *data, size_t *dataLength)
{
  FRDSecureTransportConnection *theConnection = (__bridge FRDSecureTransportConnection *)inConnection;
  // TODO: Append to buffer.
  return(noErr);
}

static OSStatus FRDSSLWrite(SSLConnectionRef inConnection, const void *data, size_t *dataLength)
{
  FRDSecureTransportConnection *theConnection = (__bridge FRDSecureTransportConnection *)inConnection;
  // TODO: Send data.
  return(noErr);
}

```

自己实现一个支持 SNI 的 NSURLSession 如此麻烦，中间比较容易出现异常和 BUG，这里推荐使用偷懒的做法。

通过 NSURLSessionDataTask 设置 SSLPeerName

```
- (void)frd_setSSLPeerName:(nullable NSString *)SSLPeerName
{
  NSDictionary<NSString *, id> *const SSLSettings = [self valueForKey:@"_sslSettings"];
  NSMutableDictionary<NSString *, id> *const mutableSSLSettings = (SSLSettings != nil) ? [SSLSettings mutableCopy] : [[NSMutableDictionary<NSString *, id> alloc] initWithCapacity:1];

  if (SSLPeerName != nil) {
    [mutableSSLSettings setObject:SSLPeerName forKey:(__bridge NSString *)kCFStreamSSLPeerName];
  } else {
    [mutableSSLSettings removeObjectForKey:(__bridge NSString *)kCFStreamSSLPeerName];
  }

  [self setValue:mutableSSLSettings forKey:@"_sslSettings"];
}

```

通过 NSURLProtocol 截获所有的请求之后，客户端包装一个新的 NSURLSessionDataTask 来发送 Request。

```
NSURLSessionTask *dataTask = [[[self class] sharedDemux] dataTaskWithRequest:mutableRequest delegate:self modes:self.modes];

if (addresses != nil && addresses.count > 0) {
  if (mutableRequest.URL.scheme != nil && [mutableRequest.URL.scheme caseInsensitiveCompare:@"https"] == NSOrderedSame) {
    [dataTask frd_setSSLPeerName:[mutableRequest valueForHTTPHeaderField:@"Host"]];
  }
}

[dataTask resume];

```

这样就解决了一个 IP 有多个证书的情况。
具体 NSURLProtocol 截获的过程可以参考 `FRDDNSURLProtocol.m` 文件。


## 参考

+ [域名服务器缓存污染](https://zh.wikipedia.org/wiki/%E5%9F%9F%E5%90%8D%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%BC%93%E5%AD%98%E6%B1%A1%E6%9F%93)

+ [Using the Secure Socket Layer for Network Communication](https://developer.apple.com/documentation/security/secure_transport/using_the_secure_socket_layer_for_network_communication)

+ [CFNetwork Programming Guide](https://developer.apple.com/library/content/documentation/Networking/Conceptual/CFNetwork/CFStreamTasks/CFStreamTasks.html#//apple_ref/doc/uid/TP30001132-CH6-SW1)

+ [阿里云 HTTPS SNI 业务场景说明](https://help.aliyun.com/knowledge_detail/60147.html)

+ [Github avenuecollection](https://github.com/alexbeattie/avenuecollection)

+ [FRDNetwork](https://github.intra.douban.com/iOS/FRDNetwork)
