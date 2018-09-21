from users.models import EosCode
import random
from utils.cache import set_cache, get_cache


def recache_eos_code():
    """
    重新生成EOS Code缓存
    """
    index = get_cache(EosCode.objects.key_daily_eos_code_index)
    if index is not None and index != -1:
        print('正在更新已使用的充值码状态')
        cache_eos_codes = get_cache(EosCode.objects.key_daily_eos_code)
        index_ids = []
        for i in range(index + 1):
            cache_eos_code = cache_eos_codes[i]
            index_ids.append(int(cache_eos_code[1]))
        EosCode.objects.filter(id__in=index_ids).update(is_used=True)
        print('共更新', len(index_ids), '条充值码')

    print('正在随机获取EOS充值码')
    eos_codes = EosCode.objects.filter(is_used=False, is_good_code=False)[0:100000]
    print('获取到 ' + str(len(eos_codes)) + ' 条充值码')

    max_size = 1000
    random_codes = []
    while True:
        idx = random.randint(1, len(eos_codes))
        eos_code = eos_codes[idx]
        eos_code_value = [eos_code.code, eos_code.id]

        if eos_code_value in random_codes:
            continue

        random_codes.append(eos_code_value)

        if len(random_codes) >= max_size:
            break

    set_cache(EosCode.objects.key_daily_eos_code, random_codes)
    set_cache(EosCode.objects.key_daily_eos_code_index, -1)
    print('recache_eos_code success')
