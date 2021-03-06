# -*- coding: UTF-8 -*-
"""
接口错误码
"""
API_0_SUCCESS = 0
API_403_ACCESS_DENY = 403
API_404_NOT_FOUND = 404
API_405_WAGER_PARAMETER = 405
API_406_LOGIN_REQUIRE = 406
API_10101_SYSTEM_PARAM_REQUIRE = 10101
API_10102_SIGNATURE_ERROR = 10102
API_10103_REQUEST_EXPIRED = 10103
API_10104_PARAMETER_EXPIRED = 10104
API_10105_NO_REGISTER = 10105
API_10106_TELEPHONE_REGISTER = 10106
API_10107_INVITATION_CODE_INVALID = 10107
API_10108_INVITATION_CODE_NOT_NOME = 10108
API_10109_INVITATION_CODE_NOT_NONENTITY = 10109
API_10110_REQUEST_REPLY_DENY = 10110
API_20101_TELEPHONE_ERROR = 20101
API_20102_TELEPHONE_REGISTERED = 20102
API_20103_TELEPHONE_UNREGISTER = 20103
API_20104_LOGIN_ERROR = 20104
API_20105_GOOGLE_RECAPTCHA_FAIL = 20105
API_20401_TELEPHONE_ERROR = 20401
API_20402_INVALID_SMS_CODE = 20402
API_20403_SMS_CODE_EXPIRE = 20403
API_20404_SAME_IP_ERROR = 20404
API_20405_CAPTCHA_ERROR = 20405
API_20601_PASS_CODE_ERROR = 20601
API_20602_PASS_CODE_LEN_ERROR = 20602
API_20701_USED_PASS_CODE_ = 20701
API_20702_USED_PASS_CODE_ERROR = 20702
API_20801_PASS_CODE_ERROR = 20801
API_20802_PASS_CODE_LEN_ERROR = 20802
API_21401_USER_PASS_CODE_ERROR = 21401
API_30201_ALREADY_SING = 30201
API_30202_PRESENTATION_FAIL = 30202
API_40101_SMS_CODE_ID_INVALID = 40101
API_40102_SMS_CODE_EXPIRED = 40102
API_40103_SMS_CODE_INVALID = 40103
API_40104_SMS_PERIOD_INVALID = 40104
API_40105_SMS_WAGER_PARAMETER = 40105
API_40106_SMS_PARAMETER = 40106
API_40107_SMS_PLEASE_REGAIN = 40107
API_50101_QUIZ_OPTION_ID_INVALID = 50101
API_50102_WAGER_INVALID = 50102
API_50103_WAGER_LIMITED = 50103
API_50104_USER_COIN_NOT_METH = 50104
API_50105_USER_COIN_NOT_GGTC = 50105
API_50106_PARAMETER_EXPIRED = 50106
API_50107_USER_BET_TYPE_ID_INVALID = 50107
API_50108_THE_GAME_HAS_STARTED = 50108
API_50109_BET_LIMITED = 50109
API_50201_BET_LIMITED = 50201
API_50202_MARKSIX_BET_LIMITED = 50202
API_50203_BET_ERROR = 50203
API_50204_BET_ERROR = 50204
API_50204_BET_CLOSED = 50205
API_50206_BET_COLOR_OVER = 50206
API_60101_USER_INVITATION_MONEY = 60101
API_60102_LUCK_DRAW_FREQUENCY_INSUFFICIENT = 60102
API_60103_INTEGRAL_INSUFFICIENT = 60103
API_70101_USER_PRESENT_AMOUNT_GT = 70101
API_70102_USER_PRESENT_AMOUNT_EZ = 70102
API_70103_USER_PRESENT_AMOUNT_LC = 70103
API_70104_USER_PRESENT_ADDRESS_EX = 70104
API_70105_USER_PRESENT_ADDRESS_EY = 70105
API_70106_USER_PRESENT_ADDRESS_NAME = 70106
API_70107_USER_PRESENT_BALANCE_NOT_ENOUGH = 70107
API_70108_USER_PRESENT_PASSWORD_ERROR = 70108
API_70109_USER_PRESENT_ADDRESS_ERROR = 70109
API_70201_USER_RECHARGE_ADDRESS = 70201
API_70202_USER_RECHARGE_AMOUNT = 70202
API_70203_PROHIBIT_LOGIN = 70203
API_70204_ETH_UNQUALIFIED_CONVERTIBILITY = 70204
API_70205_ETH_NOT_SUFFICIENT_FUNDS = 70205
API_70206_CONVERTIBLE_GSG_INSUFFICIENT = 70206
API_70207_REACH_THE_UPPER_LIMIT = 70207
API_70208_NO_REDEMPTION = 70208
API_70209_ACTIVITY_HAS_NOT_STARTED = 70209
API_70210_ACTIVITY_ENDS = 70210
API_80101_STOP_BETTING = 80101
API_90101_DRAGON_TIGER_NO_BET = 90101
API_90102_DRAGON_TIGER_NO_BET = 90102
API_90103_DRAGON_TIGER_NO_BET = 90103
API_90104_DRAGON_TIGER_NO_BET = 90104
API_100101_USER_MOBILE_COIN = 100101
API_100102_USER_MOBILE_COIN = 100102
API_100103_USER_MOBILE_COIN = 100103
API_110101_USER_BANKER = 110101
API_110102_USER_BANKER = 110102
API_110103_USER_BANKER = 110103
API_110104_USER_BANKER = 110104
API_110105_BACKEND_BANKER = 110105
API_110106_BACKEND_BANKER = 110106
API_110107_BACKEND_BANKER = 110107
API_110108_BACKEND_BANKER = 110108
API_110109_BACKEND_BANKER = 110109
API_110110_BACKEND_BANKER = 110110
API_110111_BACKEND_BANKER = 110111
API_110112_BACKEND_BANKER = 110112
API_110113_BACKEND_BANKER = 110113
API_110114_BACKEND_BANKER = 110114
API_110115_BACKEND_BANKER = 110115
API_110116_BACKEND_BANKER = 110116

API_ERROR_MESSAGE = {
    API_0_SUCCESS: '请求成功',
    API_403_ACCESS_DENY: '无访问权限',
    API_404_NOT_FOUND: '无数据',
    API_406_LOGIN_REQUIRE: '未登录，禁止访问',
    API_405_WAGER_PARAMETER: '无效参数',
    API_70209_ACTIVITY_HAS_NOT_STARTED: '活动未开始',
    API_70210_ACTIVITY_ENDS: '活动已结束',
    API_10101_SYSTEM_PARAM_REQUIRE: '系统级参数错误',
    API_10102_SIGNATURE_ERROR: '签名值错误',
    API_10103_REQUEST_EXPIRED: '请求已失效',
    API_10104_PARAMETER_EXPIRED: '参数错误',
    API_10105_NO_REGISTER: '未注册',
    API_10106_TELEPHONE_REGISTER: '账号已被注册',
    API_10107_INVITATION_CODE_INVALID: '该邀请码已达上限，找个新的吧',
    API_10108_INVITATION_CODE_NOT_NOME: '邀请码不能为空',
    API_10109_INVITATION_CODE_NOT_NONENTITY: '邀请码不存在',
    API_10110_REQUEST_REPLY_DENY: '请勿重复请求',
    API_20101_TELEPHONE_ERROR: '手机号码格式错误',
    API_20102_TELEPHONE_REGISTERED: '该手机号码已被注册',
    API_20103_TELEPHONE_UNREGISTER: '该手机号码未注册',
    API_20104_LOGIN_ERROR: '手机号码或密码错误',
    API_20105_GOOGLE_RECAPTCHA_FAIL: '校验失败',
    API_20401_TELEPHONE_ERROR: '请输入手机号',
    API_20402_INVALID_SMS_CODE: '短信验证码错误',
    API_20403_SMS_CODE_EXPIRE: '验证码已过期',
    API_20404_SAME_IP_ERROR: '同一IP不能重复注册',
    API_20405_CAPTCHA_ERROR: '验证码错误',
    API_20601_PASS_CODE_ERROR: '请输入密保',
    API_20602_PASS_CODE_LEN_ERROR: '请输入6位以上密保',
    API_20701_USED_PASS_CODE_: '请输入原密保',
    API_20702_USED_PASS_CODE_ERROR: '原密保错误',
    API_20801_PASS_CODE_ERROR: '请客输入新密保',
    API_20802_PASS_CODE_LEN_ERROR: '请输入6位以上新密保',
    API_21401_USER_PASS_CODE_ERROR: '密保错误',
    API_30201_ALREADY_SING: '您已签到',
    API_30202_PRESENTATION_FAIL: '打款失败',
    API_40101_SMS_CODE_ID_INVALID: '无效的code_id',
    API_40102_SMS_CODE_EXPIRED: '验证码已过期',
    API_40103_SMS_CODE_INVALID: '验证码错误',
    API_40104_SMS_PERIOD_INVALID: '短信间隔期未到',
    API_40105_SMS_WAGER_PARAMETER: '无效参数',
    API_40106_SMS_PARAMETER: '请输入有效验证码',
    API_40107_SMS_PLEASE_REGAIN: '输入错误超过5次,请重新获取验证码',
    API_50101_QUIZ_OPTION_ID_INVALID: '无效的投注选项',
    API_50102_WAGER_INVALID: '无效的赌注',
    API_50103_WAGER_LIMITED: '单次下注超过上限',
    API_50104_USER_COIN_NOT_METH: '资金不足',
    API_50106_PARAMETER_EXPIRED: '参数错误',
    API_50107_USER_BET_TYPE_ID_INVALID: '无效竞猜',
    API_50108_THE_GAME_HAS_STARTED: '比赛已开始！',
    API_50109_BET_LIMITED: '单场比赛投注已达上限！',
    API_50201_BET_LIMITED: '投注号码不合法！',
    API_50202_MARKSIX_BET_LIMITED: '玩法投注已达上限！',
    API_50203_BET_ERROR: '投注注数不合法！',
    API_50204_BET_ERROR: '投注金额不合法！',
    API_50204_BET_CLOSED: '投注时间已过！',
    API_50206_BET_COLOR_OVER: '至多选择两个波色',
    API_60101_USER_INVITATION_MONEY: '奖金已经领光',
    API_60102_LUCK_DRAW_FREQUENCY_INSUFFICIENT: '抽奖次数不足',
    API_60103_INTEGRAL_INSUFFICIENT: 'GSG不足',
    API_70101_USER_PRESENT_AMOUNT_GT: '提现金额大于用户金额',
    API_70102_USER_PRESENT_AMOUNT_EZ: '提现金额小于或等于0',
    API_70103_USER_PRESENT_AMOUNT_LC: '提现金额小于提现限制最小金额数',
    API_70104_USER_PRESENT_ADDRESS_EX: '提现地址已被其它用户绑定',
    API_70105_USER_PRESENT_ADDRESS_EY: '提现地址不能为空',
    API_70106_USER_PRESENT_ADDRESS_NAME: '地址名不能为空',
    API_70107_USER_PRESENT_BALANCE_NOT_ENOUGH: '余额不足,请充值',
    API_70108_USER_PRESENT_PASSWORD_ERROR: '密码错误',
    API_70109_USER_PRESENT_ADDRESS_ERROR: '不是有效的以太坊地址',
    API_70201_USER_RECHARGE_ADDRESS: '充值地址不能为空',
    API_70202_USER_RECHARGE_AMOUNT: '充值金额需大于0',
    API_70203_PROHIBIT_LOGIN: '该账号已禁止登录',
    API_70204_ETH_UNQUALIFIED_CONVERTIBILITY: '单次兑换数量不得小于0.01',
    API_70205_ETH_NOT_SUFFICIENT_FUNDS: '用户ETH余额不足',
    API_70206_CONVERTIBLE_GSG_INSUFFICIENT: '可兑换GSG不足',
    API_70207_REACH_THE_UPPER_LIMIT: '一天兑换不能超过5个ETH',
    API_70208_NO_REDEMPTION: '没有兑换资格',
    API_80101_STOP_BETTING: '该期已封盘',
    API_90101_DRAGON_TIGER_NO_BET: '尚未接受下注',
    API_90102_DRAGON_TIGER_NO_BET: '停止下注-等待开盘',
    API_90103_DRAGON_TIGER_NO_BET: '该局已开奖',
    API_90104_DRAGON_TIGER_NO_BET: '目前下注金额不得大于 %s',
    API_100101_USER_MOBILE_COIN: '该币暂不支持转账',
    API_100102_USER_MOBILE_COIN: '该用户不存在',
    API_100103_USER_MOBILE_COIN: '不可选自己为收款人',
    API_110101_USER_BANKER: '比赛或已开始！该状态不接受下注！',
    API_110102_USER_BANKER: '不在接受做庄时间！',
    API_110103_USER_BANKER: '剩余可认购额不足！',
    API_110104_USER_BANKER: '该俱乐部暂不支持联合做庄！',
    API_110105_BACKEND_BANKER: '该用户余额不足，设置局头失败！',
    API_110106_BACKEND_BANKER: '为了计算不出错，局头做庄押金必须是整数！',
    API_110107_BACKEND_BANKER: '该俱乐部已有有效局头，不支持添加新局头！',
    API_110108_BACKEND_BANKER: '该俱乐部已开启散户做庄，不支持局头做庄！',
    API_110109_BACKEND_BANKER: '该用为机器人不支持做局头！',
    API_110110_BACKEND_BANKER: '该手机号未注册！',
    API_110111_BACKEND_BANKER: '该俱乐部存在固定局头，不容许开启散户！',
    API_110112_BACKEND_BANKER: '该俱乐部做庄存在未开奖散户，暂不容许开启固定局头，请等开奖完成！',
    API_110113_BACKEND_BANKER: '该俱乐部不容许设置固定局头！',
    API_110114_BACKEND_BANKER: '您不是该俱乐部局头！',
    API_110115_BACKEND_BANKER: '该用户余额不足！',
    API_110116_BACKEND_BANKER: '该用户不是该俱乐部局头！',

}
