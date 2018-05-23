# -*- coding: UTF-8 -*-

import copy


def myprint(*args):
    print(*args)
    pass


class Game(object):
    alpha = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']

    def __init__(self, release_factor, supplement, max_wager, oddses):
        myprint('-' * 30, 'init start')
        self._release_factor = release_factor
        myprint('影响因素值 = ', self._release_factor)
        self._supplement = supplement
        myprint('发起竞猜所需猜币 = ', self._supplement)
        self._max_wager = max_wager
        myprint('单次最大下注数 = ', self._max_wager)
        self._oddses = copy.deepcopy(oddses)
        myprint('实时赔率 = ', self._oddses)
        self._bets = []
        # for simplify calculate
        for i, odds in enumerate(self._oddses):
            self._bets.append([[0., odds]])

        myprint('赔率切割 = ', self._bets)
        myprint('-' * 30, 'init end')

    def bet(self, pool, pays):
        new_oddses = []
        max_odds = max(self._oddses)
        min_odds = min(self._oddses)
        for i, pay in enumerate(pays):
            supple = pay - self._release_factor * pool
            print('supple = ', supple)

            delta = .01 * max_odds / min_odds
            print('delta = ', delta)

            # 庄家赔钱的选项，通过减少赔率让大家少买
            if supple > self._max_wager:
                odds = self._oddses[i] - delta
            # 反之
            elif -supple > self._max_wager:
                odds = self._oddses[i] + delta
            else:
                odds = self._oddses[i]

            # 避免赔率出现负数
            odds = odds if odds > 1 else 1.01
            new_oddses.append(odds)
        self._oddses = new_oddses

        return

    def bet_bak(self, index, wager):
        myprint('-' * 30, 'bet start')
        myprint('下注选项index:', index)
        myprint('下注金额wager:', wager)
        self._bets[index].append([wager, self._oddses[index]])
        myprint('下注后赔率切割self._bets = ', self._bets)

        pool = 0.
        odd_pools = []
        pays = []
        for nbet in self._bets:
            pay = 0.
            odd_pool = 0.
            for wager, odds in nbet:
                pool += wager
                odd_pool += wager
                pay += wager * odds
            odd_pools.append(odd_pool)
            pays.append(pay)

        myprint("奖池总数pool:", pool)
        myprint("各选项下注猜币数odd_pools:", odd_pools)
        myprint("各选项产出猜币数pays:", pays)
        myprint("目前赔率self._oddses:", self._oddses)

        new_oddses = []
        max_odds = max(self._oddses)
        min_odds = min(self._oddses)
        myprint('最大赔率max_odds = ', max_odds)
        myprint('最小赔率min_odds = ', min_odds)
        for i, pay in enumerate(pays):
            myprint('选项', self.alpha[i], '#' * 30)
            myprint('下注记录self._bets[i]: ', self._bets[i])
            myprint('可收入pay:', pay)
            supple = pay - self._release_factor * pool
            myprint('Supple:', supple)

            #            delta = .01 * supple / float(self._max_wager)
            delta = .01 * max_odds / min_odds
            myprint('delta = ', delta)
            #            odds = self._oddses[i] - delta
            # 庄家赔钱的选项，通过减少赔率让大家少买
            if supple > self._max_wager:
                odds = self._oddses[i] - delta
                if odds <= 1:
                    odds = 1.01
            # 反之
            elif -supple > self._max_wager:
                odds = self._oddses[i] + delta
            else:
                odds = self._oddses[i]
            new_oddses.append(odds)
        myprint('-' * 30, 'bet end')
        myprint("新赔率new_oddses:", new_oddses)
        self._oddses = new_oddses

        return

    def get_oddses(self):
        oddses = []
        for odd in self._oddses:
            oddses.append(round(odd, 2))
        return oddses


def find_max_index(alist):
    idx = 0
    max = alist[idx]
    for i, v in enumerate(alist):
        if v > max:
            max = v
            idx = i
    return idx


def game2():
    import random
    g = Game(0.9, 1000000, 5000, [1.8, 1.8])
    while True:
        i = find_max_index(g._oddses)
        g.bet(i, random.randint(0, 5000))
        t = input()
        if t == 'q':
            break


def game():
    import random
    g = Game(0.5, 1000000, 5000, [1.8, 1.8])
    while True:
        g.bet(random.choice([0, 1]), random.randint(0, 5000))
        #        g.bet(0, random.randint(0, 5000))
        t = input()
        if t == 'q':
            break


if __name__ == '__main__':
    game2()
#    game()
