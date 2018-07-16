# -*- coding: utf-8 -*-
import random
from decimal import Decimal

###################产生随机数###################
###################第一个数随机产生，第二个使用平均数求出###################
#count 数字的个数
#average 平均数
#begin 起始区间
#end 结束区间
def float_random (count, average, begin, end):
    numarr = [0 for x in range(2)]
    i = 0
    while (1):
      num = random.uniform(begin, end)
      #取两位小数
      num_first = round(num, 2)

      #第二个数
      num_second = average * 2 - num_first

      if (num_second >= begin and num_second <= end):
          numarr[i] = num_first
          i = i + 1
          numarr[i] = num_second
          break

    return numarr

###################主函数调用产生实型随机数###################
def generate_random_float(count, average):
  """
  :param count 生成总数
  :param average 平均值
  """
  if count == 1:
    return [Decimal('%0.2f' % average)]

  begin = 0.01    # 最小值
  end = 5         # 最大值
  numarr_count = 0
  numarr = [begin for x in range(count)]
  for i in range (int(count / 2)):
      lists = float_random(count, average, begin, end)
      j = 0
      for j in range (len(lists)):
           numarr[numarr_count] = Decimal('%0.2f' % lists[j])
           numarr_count += 1
  random.shuffle(numarr)
  return numarr

def get_robot_exchange(total_exchange, total_robot, exchange_rate):
    total_exchange = float(total_exchange)
    exchange_rate = float(exchange_rate)

    if total_exchange <= 0:
        return False

    print('剩余GSG总数 total_exchange = ', total_exchange)
    print('剩余机器人总数 total_robot = ', total_robot)
    print('兑换比例 exchange_rate = 1:', exchange_rate)

    avg = total_exchange / float(exchange_rate * total_robot)  # 平均值
    avg = float(round(avg, 2))
    print('avg = ', avg)
    if avg >= 5:
        avg = random.randint(1, 4)
    if avg * exchange_rate > total_exchange:
        avg -= 0.01
    avg = float(round(avg, 2))
    print('round avg = ', avg)
    print('')
    random_exchange = generate_random_float(total_robot, avg)

    if len(random_exchange) <= 20:
        current_exchange = max(random_exchange)
    else:
        secure_random = random.SystemRandom()
        current_exchange = secure_random.choice(random_exchange)

    return float(current_exchange)

# initial_sum = 2000000
# initial_robot = 666
# eth_price = 3000
# gsg_price = 0.3
#
# # 模拟真实用户情况
# real_users = random.randint(1, 5)
#
# len_robot = initial_robot + 1
# for i in range(1, len_robot):
#   exchange_rate = round(eth_price / gsg_price, 2)
#
#   # 模拟真实用户
#   current_exchange = 0
#   if i in [80, 90, 98]:
#     current_exchange = random.randint(1, 300) / 100
#   else:
#     current_exchange = get_robot_exchange(initial_sum, initial_robot, exchange_rate)
#
#   if current_exchange is False:
#       continue
#
#   initial_sum -= int(current_exchange * exchange_rate)
#   initial_robot -= 1
#
#   # 调整eth_price、gsg_price
#   eth_price += random.randint(-100, 100)
#   gsg_price += random.randint(-100, 100) / 10000
#
# print('initial_sum = ', initial_sum)
# print('initial_robot = ', initial_robot)

