---
layout: post
title: 微信支付Python客户端
---

微信支付后端服务是通过财付通实现，所以在通过微信支付审核之后，系统会发送微信支付相关 app_key，app_secret 还有对应的财付通账号。邮件里会包含财付通账号信息，证书文件。

#### 微信支付方式

微信支付支持公众号支付和 APP 支付，公众号分为原生支付和 JS 支付，APP 支付自然就是移动应用通过微信 SDK 调用微信应用进行支付。这里讲一下公众号支付的用处，公众号支付中的原生支付，是指通过将商品信息通过二维码的方式，用户通过二维码扫描唤起微信应用进行支付；JS 支付是指通过用户订阅公众号，在微信页面向用户推广商品，用户可以通过商户的 H5 页面在微信内浏览器中完成支付。

#### 微信支付申请流程

商户可以通过微信公众号平台和微信开放平台分别申请公众号支付和 APP 支付。每一种方式都对应一个 app_id, app_secret。对于这点我开始理解的时候也非常吃力，为什么不能整合到一起？不过这两种支付方式可以对应同一个财付通账号，这一点还是让人欣慰的。

#### 支付和退款流程

微信支付流程非常简单，签名方式都很普通，不过退款流程是通过财付通进行的。

1. 原生支付
    流程：生成商品二维码 -> 用户扫描 -> 微信后端请求商户后端获取商品信息(Package) -> 微信支付 -> 支付成功回调商户后端 -> 商户后端收到回调 -> 发货
    获取商品信息的地址是在申请微信支付的时候必须填写的内容，后续可以修改。

2. APP 支付
    流程：获取 token -> 生成预支付订单 -> 唤起微信 SDK -> 微信支付 -> 支付成功回调商户后端 -> 商户后端收到回调 -> 发货

3. 退款
    退款比较简单，没有回调，请求后阻塞返回退款结果。

#### 签名

牵扯到两种签名方法 SHA1 和 MD5。

1. 原生支付
    生成二维码的原始内容
    ```python
    def native_payment_url(self, order):
        params = {}
        params['appid'] = ''
        params['timestamp'] = ''
        params['noncestr'] = ''
        params['productid'] = order.id
        params['sign'] = sign_by_appkey(params)
        return 'weixin://wxpay/bizpayurl' + ? + urlencode(params)

    def sign_by_appkey(params):
        data = params.copy()
        data['appkey'] = ''
        base = '&'.join(['%s=%s' % (key, data[key]) for key in sorted(data)])
        return hashlib.sha1(base).hexdigest()
    ```

    获取商品信息
    同样是 SHA1 签名，签名字段 appid、appkey、package、timestamp、noncestr、retcode、reterrmsg

    这里说一下 package 字段生成方式：

    ```python
    def get_package(self, order):
        params = {}
        params['bank_type'] = 'WX'
        params['body'] = '电影票务支付'
        params['partner'] = ''
        params['out_trade_no'] = order.id
        params['total_fee'] = int(order.amount * 100)
        params['fee_type'] = '1'
        params['notify_url'] = '' # 商户通知地址，可自定义
        params['spbill_create_ip'] = order.ip
        params['time_start'] = order.created_at
        params['time_expire'] = order.expired_at
        params['input_charset'] = 'UTF-8'
        signature = sign_by_partnerkey(params)
        package = '&'.join([urlencode({key:params[key]}) for key in sorted(params)])
        return package + '&sign=%s' % signature

    def sign_by_partnerkey(params):
        base = '&'.join(['%s=%s' % (key, data[key]) for key in sorted(data)])
        base += '&key=' + PARTNER_KEY
        return hashlib.md5(base).hexdigest()
    ```

待续...
