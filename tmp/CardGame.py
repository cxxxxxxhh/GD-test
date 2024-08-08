# -*- coding: utf-8 -*-
"""
Created on Sun May 26 17:00:24 2024

@author: 天昊
"""

import random
import pygame
from GDModel import GDModel
import numpy as np
import pickle
import itertools
import tensorflow as tf
import math

from collections import Counter, OrderedDict

from typing import Optional


def find_element_occurred_twice(cards):
    # 创建一个字典来计数每个元素的出现次数
    count = {}

    # 遍历牌的列表，统计每个元素的出现次数
    for card in cards:
        card = str(card)
        if card in count:
            count[card] += 1
        else:
            count[card] = 1

    # 检查哪些元素出现了两次
    for key in count:
        if count[key] == 2:
            return key[-1]  # 返回出现两次的元素的最后一个字符

    return None  # 如果没有找到符合条件的元素，则返回 None


def get_info_for_penalty(handcards, rank):
    single_cards = []
    pairs = []

    card_value_s2v = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                      "Q": 12, "K": 13, "A": 14, "B": 16, "R": 17}
    card_value_s2v2 = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                       "Q": 12, "K": 13, "B": 16, "R": 17}
    rank_card = 'H' + str(rank)
    card_value_s2v[rank_card[-1]] = 15

    # Remove the larger card
    remove_list = [rank_card[-1], 'B', 'R']

    sorted_handCards = sorted(
        handcards, key=lambda card: card_value_s2v[card[1]])

    card_counts = Counter(card[1:] for card in sorted_handCards)

    # Search all 'single'
    single_cards = [
        card for card in sorted_handCards if card_counts[card[1:]] == 1]

    # Search all 'pairs'
    pairs = [card for card in sorted_handCards if card_counts[card[1:]] == 2]
    pairs = list(OrderedDict.fromkeys(pairs))

    sorted_handCards_straight = sorted(
        handcards, key=lambda card: card_value_s2v2[card[1]])

    def find_straights(sorted_handCards_straight, min_length=5):
        if not sorted_handCards_straight:
            return []
        straights = []
        current_straight = [sorted_handCards_straight[0]]

        for i in range(1, len(sorted_handCards_straight)):
            if sorted_handCards_straight[i][1:] == sorted_handCards_straight[i - 1][1:]:
                continue
            if card_value_s2v2[sorted_handCards_straight[i][1:]] == card_value_s2v2[current_straight[-1][1:]] + 1:
                current_straight.append(sorted_handCards_straight[i])
            else:
                if len(current_straight) >= min_length:
                    straights.append(current_straight)
                current_straight = [sorted_handCards_straight[i]]

        if len(current_straight) >= min_length:
            straights.append(current_straight)
        return straights

    single_cards = [
        card for card in single_cards if card[1:] not in remove_list]
    pairs = [card for card in pairs if card[1:] not in remove_list]
    return single_cards, pairs, find_straights(sorted_handCards_straight, min_length=5)


def get_score_by_situation(situation: str, level: str, t: str, bomb_size: Optional[int]):
    if t == "PASS":
        return 0
    origin_rank = ['2', '3', '4', '5', '6', '7', '8',
                   '9', 'T', 'J', 'Q', 'K', 'A', 'B', 'R', 'JOKER']
    if not (t in ['Straight', 'StraightFlush', 'ThreeWithTwo', 'TwoTrips', 'ThreePair']):
        idx = origin_rank.index(level)
        origin_rank.pop(idx)
        origin_rank.insert(12, level)
    else:
        origin_rank.pop(12)
        origin_rank.insert(0, 'A')
    size = len(origin_rank)
    addition = [0] * size
    if situation == 'start':
        if t in ['Single']:
            for i in range(size):
                addition[i] = max(0.05 - i * 0.01, 0)
        elif t in ['Pair', 'Trips']:
            for i in range(size):
                addition[i] = max(0.04 - i * 0.015, -0.01)
        elif t in ['ThreeWithTwo', 'Straight']:
            for i in range(size):
                addition[i] = max(0.07 - i * 0.02, 0.01)
        elif t not in ['StraightFlush', 'Bomb']:
            for i in range(size):
                addition[i] = 0.2 - i * 0.035
    elif situation == 'middle':
        if t in ['Single']:
            for i in range(size):
                addition[i] = max(0.03 - i * 0.01, 0)
        elif t in ['Pair', 'Trips']:
            for i in range(size):
                addition[i] = max(0.02 - i * 0.01, 0)
        elif t in ['ThreeWithTwo', 'Straight']:
            for i in range(size):
                addition[i] = max(0.12 - i * 0.015, 0.03)
        elif t not in ['StraightFlush', 'Bomb']:
            for i in range(size):
                addition[i] = max(0.1 - i * 0.04, -0.02)
    elif situation == 'end':
        if t == 'Bomb' or t == 'StraightFlush':
            for i in range(size):
                addition[i] = max(0.1 - i * 0.02, 0.05)
        elif t in ['Single', 'Pair', 'Trips']:
            for i in range(size):
                addition[i] = min(i * 0.01, 0.03)
        else:
            for i in range(size):
                addition[i] = min(i * 0.01, 0.05)
    elif situation == 'almost over':
        if t == 'Bomb' or t == 'StraightFlush':
            for i in range(size):
                addition[i] = i * 0.06 + (bomb_size - 4) * 0.1
            addition[-1] += 1.0
        elif t in ['Straight', 'ThreeWithTwo', 'TwoTrips', 'ThreePair']:
            for i in range(size):
                addition[i] = min(i * 0.05, 0.5)
    return dict(zip(origin_rank, addition))


STATE_NUM = [20, 13, 7]

rank2num = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
            'K': 13, 'A': 14, 'SB': 16, 'HR': 17}

num2rank = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
            13: 'K', 14: 'A', 16: 'SB', 17: 'HR'}


WIDTH = 1024
HEIGHT = 768
green = (0, 200, 0)
red = (200, 0, 0)
yellow = (240, 220, 0)
brightYellow = (255, 255, 0)
brightGreen = (0, 255, 0)
brightRed = (255, 0, 0)


def arrange(L):
    L.sort(key=lambda card: (card.realRank, card.suit))


class Game(object):
    def __init__(self, teamALevel=2, teamBLevel=2):
        self.teamALevel = teamALevel
        self.teamBLevel = teamBLevel
        self.players = []
        self.winners = []
        self.losers = []
        self.startPage = True
        self.settingsPage = False
        self.infoPage = False
        self.introPage = False
        self.rulesPage = False
        self.thePlayPage = False
        self.offlineMode = False
        self.endPage = False
        self.cardsOnTable = []
        self.lastPlayer = None
        self.isOver = (
            len([player for player in self.players if player.isOver]) > 2)
        self.nextRanking = 1
        self.wildRank = 2
        self.AISpeed = 500
        self.bg = "bg2.jpg"

# 设置出牌速度
    def setAISpeed(self):
        try:
            with open("settings.txt", "rt") as f:
                self.AISpeed = int(f.read().split()[0])
        except:
            pass

# 设置背景颜色
    def setBg(self):
        try:
            with open("settings.txt", "rt") as f:
                self.bg = f.read().split()[1]
        except:
            pass

# 画背景
    def drawBg(self, screen):
        bg = pygame.image.load(self.bg)
        screen.blit(bg, (0, 0))

# 画back按钮
    def drawBackButton(self, screen):
        font = pygame.font.Font(None, 30)
        self.backButton = pygame.Rect(842, 50, 100, 50)
        backText = font.render("Back", True, (0,) * 3)
        pygame.draw.rect(screen, yellow, self.backButton)
        screen.blit(backText, (865, 65))

# 画初始界面
    def drawStartPage(self):
        largeFont = pygame.font.Font(None, 100)
        font = pygame.font.Font(None, 30)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Start")
        self.offlineModeButton = pygame.Rect(
            WIDTH / 2 - 75, HEIGHT / 2 - 40, 150, 50)
        self.settingsButton = pygame.Rect(
            WIDTH / 2 - 75, HEIGHT / 2 + 70, 150, 50)
        self.infoButton = pygame.Rect(842, 667, 130, 50)
        guandanText = largeFont.render("Guan Dan", True, (255, 130, 0))
        offlineText = font.render("Offline Mode", True, (0,) * 3)
        settingsText = font.render("Settings", True, (0,) * 3)
        infoText = font.render("Information", True, (0,) * 3)
        self.drawBg(screen)
        screen.blit(guandanText, (350, 200))
        pygame.draw.rect(screen, green, self.offlineModeButton)
        screen.blit(offlineText, (WIDTH / 2 - 65, HEIGHT / 2 - 25))
        pygame.draw.rect(screen, red, self.settingsButton)
        screen.blit(settingsText, (WIDTH / 2 - 45, HEIGHT / 2 + 85))
        pygame.draw.rect(screen, yellow, self.infoButton)
        screen.blit(infoText, (850, 680))

# 如果点击settings按钮，画设置界面
    def drawSettingsPage(self, mousePos):
        font = pygame.font.Font(None, 30)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Settings")
        self.drawBg(screen)
        self.drawBackButton(screen)
        self.speed1Button = pygame.Rect(300, 200, 100, 50)
        self.speed2Button = pygame.Rect(450, 200, 100, 50)
        self.speed3Button = pygame.Rect(600, 200, 100, 50)
        self.bg1Button = pygame.Rect(300, 350, 100, 50)
        self.bg2Button = pygame.Rect(450, 350, 100, 50)
        self.bg3Button = pygame.Rect(600, 350, 100, 50)
        speedText = font.render("AI Speed: ", True, (255,) * 3)
        speed1Text = font.render("1s", True, (255,) * 3)
        speed2Text = font.render("2s", True, (255,) * 3)
        speed3Text = font.render("5s", True, (255,) * 3)
        bgText = font.render("Background: ", True, (255,) * 3)
        bg1Text = font.render("Blue", True, (255,) * 3)
        bg2Text = font.render("Green", True, (255,) * 3)
        bg3Text = font.render("Red", True, (255,) * 3)
        if self.speed1Button.collidepoint(mousePos):
            pygame.draw.rect(screen, brightGreen, self.speed1Button)
        else:
            pygame.draw.rect(screen, green, self.speed1Button)
        if self.speed2Button.collidepoint(mousePos):
            pygame.draw.rect(screen, brightGreen, self.speed2Button)
        else:
            pygame.draw.rect(screen, green, self.speed2Button)
        if self.speed3Button.collidepoint(mousePos):
            pygame.draw.rect(screen, brightGreen, self.speed3Button)
        else:
            pygame.draw.rect(screen, green, self.speed3Button)
        if self.bg1Button.collidepoint(mousePos):
            pygame.draw.rect(screen, brightGreen, self.bg1Button)
        else:
            pygame.draw.rect(screen, green, self.bg1Button)
        if self.bg2Button.collidepoint(mousePos):
            pygame.draw.rect(screen, brightGreen, self.bg2Button)
        else:
            pygame.draw.rect(screen, green, self.bg2Button)
        if self.bg3Button.collidepoint(mousePos):
            pygame.draw.rect(screen, brightGreen, self.bg3Button)
        else:
            pygame.draw.rect(screen, green, self.bg3Button)
        screen.blit(speedText, (100, 215))
        screen.blit(speed1Text, (340, 215))
        screen.blit(speed2Text, (490, 215))
        screen.blit(speed3Text, (640, 215))
        screen.blit(bgText, (100, 365))
        screen.blit(bg1Text, (327, 365))
        screen.blit(bg2Text, (470, 365))
        screen.blit(bg3Text, (631, 365))

# 画信息界面
    def drawInfoPage(self):
        font = pygame.font.Font(None, 30)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Information")
        self.drawBg(screen)
        self.drawBackButton(screen)
        self.introButton = pygame.Rect(
            WIDTH / 2 - 75, HEIGHT / 2 - 100, 150, 50)
        self.rulesButton = pygame.Rect(
            WIDTH / 2 - 75, HEIGHT / 2 + 15, 150, 50)
        self.thePlayButton = pygame.Rect(
            WIDTH / 2 - 75, HEIGHT / 2 + 130, 150, 50)
        introText = font.render("Introduction", True, (0,) * 3)
        rulesText = font.render("Rules", True, (0,) * 3)
        thePlayText = font.render("The Play", True, (0,) * 3)
        pygame.draw.rect(screen, green, self.introButton)
        pygame.draw.rect(screen, green, self.rulesButton)
        pygame.draw.rect(screen, green, self.thePlayButton)
        screen.blit(introText, (WIDTH / 2 - 65, HEIGHT / 2 - 85))
        screen.blit(rulesText, (WIDTH / 2 - 30, HEIGHT / 2 + 32))
        screen.blit(thePlayText, (WIDTH / 2 - 42, HEIGHT / 2 + 145))

# 画介绍界面
    def drawIntroPage(self):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Introduction")
        self.drawBg(screen)
        self.drawBackButton(screen)
        intro = pygame.image.load("intro.png")
        screen.blit(intro, (110, 150))

# 画规则界面
    def drawRulesPage(self):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rules")
        self.drawBg(screen)
        intro = pygame.image.load("rules.png")
        intro = pygame.transform.scale(intro, (1024, 700))
        screen.blit(intro, (0, 60))
        self.drawBackButton(screen)

# 画the play界面
    def drawThePlayPage(self):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("The Play")
        self.drawBg(screen)
        intro = pygame.image.load("thePlay.png")
        screen.blit(intro, (50, 110))
        self.drawBackButton(screen)

# 绘制结束界面
    def drawEndPage(self, game):
        largeFont = pygame.font.Font(None, 60)
        font = pygame.font.Font(None, 36)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("End")
        self.drawBg(screen)
        self.continueButton = pygame.Rect(WIDTH / 2 - 75, 600, 150, 60)
        continueText = font.render("Continue", True, (0,) * 3)
        winText = largeFont.render("WIN", True, (255,) * 3)
        loseText = largeFont.render("LOSE", True, (255,) * 3)
        winner1Text = font.render(
            f"{game.winners[0]}: No.{game.winners[0].ranking}", True, (255,) * 3)
        winner2Text = font.render(
            f"{game.winners[1]}: No.{game.winners[1].ranking}", True, (255,) * 3)
        loser1Text = font.render(
            f"{game.losers[0]}: No.{game.losers[0].ranking}", True, (255,) * 3)
        loser2Text = font.render(
            f"{game.losers[1]}: No.{game.losers[1].ranking}", True, (255,) * 3)
        pygame.draw.rect(screen, green, self.continueButton)
        screen.blit(continueText, (WIDTH / 2 - 58, 618))
        screen.blit(winText, (WIDTH / 2 - 300, 150))
        screen.blit(loseText, (WIDTH / 2 + 100, 150))
        screen.blit(winner1Text, (WIDTH / 2 - 300, 230))
        screen.blit(winner2Text, (WIDTH / 2 - 300, 280))
        screen.blit(loser1Text, (WIDTH / 2 + 100, 230))
        screen.blit(loser2Text, (WIDTH / 2 + 100, 280))

# 绘制当前双方等级
    def drawScoreboard(self, screen, game):
        font = pygame.font.Font(None, 30)
        teamAText = font.render(
            f"Team A Level: {num2rank[game.teamALevel]}", True, (255, 130, 0))
        teamBText = font.render(
            f"Team B Level: {num2rank[game.teamBLevel]}", True, (255, 130, 0))
        screen.blit(teamAText, (30, 20))
        screen.blit(teamBText, (30, 50))

# 绘制基础的四个按钮
    def drawBasics(self, screen, mousePos, game):
        font = pygame.font.Font(None, 24)
        self.passButton = pygame.Rect(WIDTH / 2 - 100, 500, 60, 30)
        self.playButton = pygame.Rect(WIDTH / 2 - 190, 500, 60, 30)
        self.hintButton = pygame.Rect(WIDTH / 2 - 10, 500, 60, 30)
        self.deseletButton = pygame.Rect(WIDTH / 2 + 80, 500, 100, 30)
        playText = font.render("Play", True, (0,) * 3)
        passText = font.render("PASS", True, (0,) * 3)
        hintText = font.render("Hint", True, (0,) * 3)
        deselectText = font.render("Deselect All", True, (0,) * 3)
        self.drawBg(screen)
        if game.turn == game.players[0]:
            if self.passButton.collidepoint(mousePos):
                pygame.draw.rect(screen, brightGreen, self.passButton)
            else:
                pygame.draw.rect(screen, green, self.passButton)
            if self.playButton.collidepoint(mousePos):
                pygame.draw.rect(screen, brightRed, self.playButton)
            else:
                pygame.draw.rect(screen, red, self.playButton)
            if self.hintButton.collidepoint(mousePos):
                pygame.draw.rect(screen, brightYellow, self.hintButton)
            else:
                pygame.draw.rect(screen, yellow, self.hintButton)
            if self.deseletButton.collidepoint(mousePos):
                pygame.draw.rect(screen, brightRed, self.deseletButton)
            else:
                pygame.draw.rect(screen, red, self.deseletButton)
            screen.blit(passText, (WIDTH / 2 - 89, 507))
            screen.blit(playText, (WIDTH / 2 - 178, 507))
            screen.blit(hintText, (WIDTH / 2 + 2, 507))
            screen.blit(deselectText, (WIDTH / 2 + 83, 507))
        self.drawBackButton(screen)
        self.drawScoreboard(screen, game)

# 发牌，决定谁先出
    def start(self):
        # Distributing cards
        self.cards = Poker(2, self)
        self.cards.shuffle()
        for i in range(27):
            for player in self.players:
                player.get(self.cards.next())
        for player in self.players:
            arrange(player.cardsInHand)
        self.turn = random.choice(self.players)
        self.numTurns = 0
        self.nextRanking = 1

# 更新级牌
    def updateResult(self):
        for p in self.players:
            if p.ranking == 1:
                self.winners.append(p)
                self.winners.append(self.players[self.players.index(p) - 2])
                self.losers.append(self.players[self.players.index(p) - 3])
                self.losers.append(self.players[self.players.index(p) - 1])
        print(self.players[0].ranking, self.players[1].ranking,
              self.players[2].ranking, self.players[3].ranking)
        if set(self.winners) == {self.players[0], self.players[2]}:
            print(self.players[0], self.players[2])
            print(self.players[0].ranking, self.players[2].ranking)
            oldlevel = self.teamALevel
            if {self.players[0].ranking, self.players[2].ranking} == {1, 2}:
                self.teamALevel += 3
            elif {self.players[0].ranking, self.players[2].ranking} == {1, 3}:
                self.teamALevel += 2
            else:
                self.teamALevel += 1
            if oldlevel == 14 and self.teamALevel > 14 and self.teamALevel == 15:
                self.teamALevel = 14
            elif oldlevel == 14 and self.teamALevel > 14 and self.teamALevel > 15:
                self.teamALevel = 2
            elif oldlevel < 14 and self.teamALevel > 14:
                self.teamALevel = 14
            self.wildRank = self.teamALevel
        if set(self.winners) == {self.players[1], self.players[3]}:
            print(self.players[1], self.players[3])
            print(self.players[1].ranking, self.players[3].ranking)
            oldlevel = self.teamBLevel
            if {self.players[1].ranking, self.players[3].ranking} == {1, 2}:
                self.teamBLevel += 3
            elif {self.players[1].ranking, self.players[3].ranking} == {1, 3}:
                self.teamBLevel += 2
            else:
                self.teamBLevel += 1
            if oldlevel == 14 and self.teamBLevel > 14 and self.teamBLevel == 15:
                self.teamBLevel = 14
            elif oldlevel == 14 and self.teamBLevel > 14 and self.teamBLevel > 15:
                self.teamBLevel = 2
            elif oldlevel < 14 and self.teamBLevel > 14:
                self.teamBLevel = 14
            self.wildRank = self.teamBLevel

# 开启新的回合，将玩家信息全部初始化
    def newRound(self):
        for p in self.players:
            p.passed = False
            p.isOver = False
            p.cardsPlayed = []
            p.cardsInHand = []
            p.remaincardNum = [27, 27, 27, 27]
            p.moves = [[], [], [], []]
            p.myPos = None
            allcards = p.allcards()
            p.playedcards = [allcards, allcards, allcards]
            p.ranking = 0
            p.action_order = []
            p.action_seq = []
        self.cardsOnTable = []
        self.lastPlayer = None
        self.start()
        self.nextRanking = 1
        self.winners = []
        self.losers = []

# 决定下一个玩家是谁
    def nextPlayer(self):
        if not self.players[self.players.index(self.turn) - 3].isOver:
            self.turn = self.players[self.players.index(self.turn) - 3]
        elif not self.players[self.players.index(self.turn) - 2].isOver:
            self.turn = self.players[self.players.index(self.turn) - 2]
        else:
            self.turn = self.players[self.players.index(self.turn) - 1]


class Card(object):
    def __init__(self, suit, rank, game):
        self.suit = suit
        self.rank = rank
        self.realRank = rank
        if rank == game.wildRank:
            self.realRank = 15
        self.image = pygame.image.load(f"pukeImage/{self}.png")
        self.isSelected = False

    def isInList(self, l):
        for ele in l:
            if self.__eq__(ele):
                return True
        return False

    def isWildCard(self):
        return self.realRank == 15 and self.suit == "H"

    def __str__(self):
        if self.rank == 10:
            rank_str = "T"
        elif self.rank == 11:
            rank_str = "J"
        elif self.rank == 12:
            rank_str = "Q"
        elif self.rank == 13:
            rank_str = "K"
        elif self.rank == 14:
            rank_str = "A"
        elif self.rank == 16:
            rank_str = "SB"
        elif self.rank == 17:
            rank_str = "HR"
        else:
            rank_str = str(self.rank)
        return f"{self.suit}{rank_str}"

    def __repr__(self):
        return self.__str__()

    def __gt__(self, other):
        return self.realRank > other.realRank

    def __ge__(self, other):
        return self.realRank >= other.realRank

    def __lt__(self, other):
        return self.realRank < other.realRank

    def __le__(self, other):
        return self.realRank <= other.rank


class Poker(object):
    # numDecks: 几副牌
    def __init__(self, numDecks, game):
        self.cards = [Card(suit, rank, game) for suit in "CDHS" for rank in range(
            2, 15) for i in range(numDecks)]
        for i in range(numDecks):
            self.cards.append(Card("", 16, game))
            self.cards.append(Card("", 17, game))
        self.current = 0

    def __str__(self):
        return str([card for card in self.cards])

    def shuffle(self):
        self.current = 0
        random.shuffle(self.cards)

    def next(self):
        card = self.cards[self.current]
        self.current += 1
        return card


class Player(object):
    def __init__(self, name, game):
        self.name = name
        self.cardsInHand = []
        self.selectedCards = []
        self.cardsPlayed = []
        self.myHandCards = self.str2dict(self.list2str(self.cardsInHand))
        self.passed = False
        self.isOver = False
        self.ranking = 0
        self.myPos = None
        self.current_rank = None
        self.greatcard = self.allcards()
        self.moves = [[], [], [], []]  # 按照p1,p2,p3,p4记录
        self.remainingcard = self.cal_remainingcard()
        self.remaincardNum = [27, 27, 27, 27]  # 按照p1,p2,p3,p4记录
        allcards = self.allcards()
        self.playedcards = [allcards, allcards, allcards]  # 按照下家、队友、上家记录
        tf.keras.backend.clear_session()
        tf.keras.backend.set_learning_phase(1)
        self.model = GDModel((567, ), (5, 216))
        with open('./train20/penalty_training-24500.ckpt', 'rb') as g:
            new_weights = pickle.load(g)
        self.model.set_weights(new_weights)
        self.action_order = []
        self.action_seq = []

    def get_currentRank(self, game):
        self.current_rank = str(num2rank[game.wildRank])

    def get_myPos(self, game):
        myIndex = game.players.index(self)
        firstTurn = game.players.index(game.turn)
        myPos = (myIndex + 4 - firstTurn) % 4
        self.myPos = myPos
        print(self.myPos)

    def allcards(self):
        AllCards = ['H2', 'S2', 'C2', 'D2',
                    'H3', 'S3', 'C3', 'D3',
                    'H4', 'S4', 'C4', 'D4',
                    'H5', 'S5', 'C5', 'D5',
                    'H6', 'S6', 'C6', 'D6',
                    'H7', 'S7', 'C7', 'D7',
                    'H8', 'S8', 'C8', 'D8',
                    'H9', 'S9', 'C9', 'D9',
                    'HT', 'ST', 'CT', 'DT',
                    'HJ', 'SJ', 'CJ', 'DJ',
                    'HQ', 'SQ', 'CQ', 'DQ',
                    'HK', 'SK', 'CK', 'DK',
                    'HA', 'SA', 'CA', 'DA',
                    'SB', 'HR'
                    ]

        playcards = {}
        for card in AllCards:
            playcards[card] = 0
        return playcards

    def cal_remainingcard(self):
        AllCards = ['H2', 'S2', 'C2', 'D2',
                    'H3', 'S3', 'C3', 'D3',
                    'H4', 'S4', 'C4', 'D4',
                    'H5', 'S5', 'C5', 'D5',
                    'H6', 'S6', 'C6', 'D6',
                    'H7', 'S7', 'C7', 'D7',
                    'H8', 'S8', 'C8', 'D8',
                    'H9', 'S9', 'C9', 'D9',
                    'HT', 'ST', 'CT', 'DT',
                    'HJ', 'SJ', 'CJ', 'DJ',
                    'HQ', 'SQ', 'CQ', 'DQ',
                    'HK', 'SK', 'CK', 'DK',
                    'HA', 'SA', 'CA', 'DA',
                    'SB', 'HR'
                    ]

        remaincards = {}

        for card in AllCards:
            remaincards[card] = 0

        for move_player in self.moves:
            for move in move_player:
                for card in AllCards:
                    remaincards[card] = remaincards[card] - move[card]

        for card in AllCards:
            remaincards[card] = 2 - self.myHandCards[card]

        return remaincards

    def list2str(self, cardlist):
        cardstr = ''
        for card in cardlist:
            cardstr += str(card)
        return cardstr

    def str2dict(self, cardstr):
        AllCards = ['H2', 'S2', 'C2', 'D2',
                    'H3', 'S3', 'C3', 'D3',
                    'H4', 'S4', 'C4', 'D4',
                    'H5', 'S5', 'C5', 'D5',
                    'H6', 'S6', 'C6', 'D6',
                    'H7', 'S7', 'C7', 'D7',
                    'H8', 'S8', 'C8', 'D8',
                    'H9', 'S9', 'C9', 'D9',
                    'HT', 'ST', 'CT', 'DT',
                    'HJ', 'SJ', 'CJ', 'DJ',
                    'HQ', 'SQ', 'CQ', 'DQ',
                    'HK', 'SK', 'CK', 'DK',
                    'HA', 'SA', 'CA', 'DA',
                    'SB', 'HR'
                    ]

        carddict = {}
        for card in AllCards:
            carddict[card] = 0

        if cardstr != 'PASS':
            for i in range(0, len(cardstr), 2):
                card = cardstr[i:i+2]
                if card in carddict:
                    carddict[card] += 1

        return carddict

    # ->[2,0,0,1,0,0,...,0]
    def dict2array(self, carddict):
        return np.array([carddict[card] for card in carddict])

    # 按照级数划分的字典
    def dict2rankdict(self, carddict):
        ranklist = ['2', '3', '4', '5', '6', '7', '8',
                    '9', 'T', 'J', 'Q', 'K', 'A', 'SB', 'HR']
        rankdict = {}
        for rank in ranklist:
            rankdict[rank] = []
        for card in carddict:
            if card in ['SB', 'HR']:
                rankdict[card] += [card]*carddict[card]
            else:
                rankdict[card[1]] += [card]*carddict[card]
        return rankdict

    # 生成等级和剩余牌数的0-1向量
    def _get_one_hot_array(self, num_left_cards, max_num_cards, flag):
        if flag == 0:     # 级数的情况
            one_hot = np.zeros(max_num_cards)
            one_hot[num_left_cards - 2] = 1
        else:
            one_hot = np.zeros(max_num_cards+1)    # 剩余的牌（0-1阵格式）
            one_hot[num_left_cards] = 1
        return one_hot

    # 返回lst中的级数是否是连续的。['A','2','3'] -> True; ['Q','K','A'] -> True; ['2','3','5'] -> Falsedef is_consecutive(lst):
    def is_consecutive(self, lst):
        rankorder = ['A', '2', '3', '4', '5', '6',
                     '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        indices = [rankorder.index(elem) for elem in lst if elem in rankorder]
        if len(indices) == len(lst) and len(set(indices)) == len(lst):
            if 0 in indices and 12 in indices:
                indices = [index if index != 0 else 13 for index in indices]
            indices.sort()
            return indices == list(range(indices[0], indices[-1]+1))
        return False

    # current_rank为str
    def get_all_single(self, carddict, current_rank):   # 1张牌
        singles = []
        for card in carddict:
            if carddict[card] != 0:
                if card[1] == current_rank:
                    rank = 15
                elif card in ['SB', 'HR']:
                    rank = rank2num[card]
                else:
                    rank = rank2num[card[1]]
                singles.append(['Single', rank, [card]])
        return singles

    def get_all_pair(self, carddict, current_rank):    # 2张牌
        # 先将逢人配拿掉，再把逢人配加到每个级数组内，最后再把多的逢人配组合删掉
        # 将牌按照级数分类
        pairs = []

        carddict1 = carddict.copy()
        wildcard = 'H'+current_rank
        wildcardnum = carddict1[wildcard]
        carddict1[wildcard] = 0
        rankdict = self.dict2rankdict(carddict1)
        for rank in rankdict:
            if rank not in ['SB', 'HR']:
                rankdict[rank] += [wildcard]*wildcardnum

        rank_has_enoughcard = [
            rank for rank in rankdict if len(rankdict[rank]) >= 2]

        for rank in rank_has_enoughcard:
            if rank == current_rank:
                ranknum = 15
            else:
                ranknum = rank2num[rank]
            pairs_combine = [
                list(combination) for combination in itertools.combinations(rankdict[rank], 2)]
            for pair in pairs_combine:
                pairs.append(['Pair', ranknum, pair])

        return pairs

    def get_all_triple(self, carddict, current_rank):   # 3张牌
        # 先将逢人配拿掉，再把逢人配加到每个级数组内，最后再把多的逢人配组合删掉
        # 将牌按照级数分类
        triples = []

        carddict1 = carddict.copy()
        wildcard = 'H'+current_rank
        wildcardnum = carddict1[wildcard]
        carddict1[wildcard] = 0
        rankdict = self.dict2rankdict(carddict1)
        for rank in rankdict:
            if rank not in ['SB', 'HR']:
                rankdict[rank] += [wildcard]*wildcardnum

        rank_has_enoughcard = [
            rank for rank in rankdict if len(rankdict[rank]) >= 3]

        for rank in rank_has_enoughcard:
            if rank == current_rank:
                ranknum = 15
            else:
                ranknum = rank2num[rank]
            triples_combine = [
                list(combination) for combination in itertools.combinations(rankdict[rank], 3)]
            for triple in triples_combine:
                triples.append(['Trips', ranknum, triple])

        return triples


# 钢板


    def get_all_plate(self, carddict, current_rank):   # 6张牌
        plates = []
        triples = self.get_all_triple(carddict, current_rank)
        wildcard = 'H'+current_rank
        for i in range(len(triples)):
            for j in range(i+1, len(triples)):
                if self.is_consecutive([triples[i][2][0][1], triples[j][2][0][1]]):
                    if {triples[i][2][0][1], triples[j][2][0][1]} == {'2', 'A'}:
                        rank = 1
                    else:
                        rank = min(rank2num[triples[i][2][0][1]],
                                   rank2num[triples[j][2][0][1]])
                    plates.append(
                        ['TwoTrips', rank, triples[i][2]+triples[j][2]])
        to_remove = []
        for plate in plates:
            if plate[2].count(wildcard) > carddict[wildcard]:
                to_remove.append(plate)
        for plate in to_remove:
            plates.remove(plate)

        return plates

    # 连对
    def get_all_tube(self, carddict, current_rank):   # 6张牌
        # 先将逢人配拿掉，再把逢人配加到每个级数组内，最后再把多的逢人配组合删掉
        # 将牌按照级数分类
        tubes = []

        carddict1 = carddict.copy()
        wildcard = 'H'+current_rank
        wildcardnum = carddict1[wildcard]
        carddict1[wildcard] = 0
        rankdict = self.dict2rankdict(carddict1)
        for rank in rankdict:
            if rank not in ['SB', 'HR']:
                rankdict[rank] += [wildcard]*wildcardnum

        rank_has_enoughcard = [
            rank for rank in rankdict if len(rankdict[rank]) >= 2]
        if len(rank_has_enoughcard) >= 3:
            combinations = list(list(combination) for combination in itertools.combinations(
                rank_has_enoughcard, 3))
            tube_ranks = [
                combination for combination in combinations if self.is_consecutive(combination)]
            for tube_rank in tube_ranks:
                if '2' in tube_rank and 'A' in tube_rank:
                    rank = 1
                else:
                    rank = min(
                        rank2num[tube_rank[0]], rank2num[tube_rank[1]], rank2num[tube_rank[2]])
                pairs_a = list(itertools.combinations(
                    rankdict[tube_rank[0]], 2))
                pairs_b = list(itertools.combinations(
                    rankdict[tube_rank[1]], 2))
                pairs_c = list(itertools.combinations(
                    rankdict[tube_rank[2]], 2))
                for x in range(len(pairs_a)):
                    for y in range(len(pairs_b)):
                        for z in range(len(pairs_c)):
                            tubes.append(
                                ['ThreePair', rank, list(pairs_a[x])+list(pairs_b[y])+list(pairs_c[z])])

        to_remove = []
        for tube in tubes:
            if tube[2].count(wildcard) > wildcardnum:
                to_remove.append(tube)
        for tube in to_remove:
            tubes.remove(tube)

        return tubes


# 三带二


    def get_all_fullhouse(self, carddict, current_rank):   # 5张牌
        fullhouses = []
        wildcard = 'H'+current_rank
        triples = self.get_all_triple(carddict, current_rank)
        pairs = self.get_all_pair(carddict, current_rank)
        for triple in triples:
            for pair in pairs:
                if pair[2] != [wildcard, wildcard]:  # 这样是五张牌的炸
                    if triple[2][0][1] != pair[2][0][1]:  # 这样是五张牌的炸
                        if triple[2][0][1] == current_rank:
                            triple_rank = 15
                        else:
                            triple_rank = rank2num[triple[2][0][1]]
                        fullhouses.append(
                            ['ThreeWithTwo', triple_rank*20, triple[2]+pair[2]])
        to_remove = []
        for fullhouse in fullhouses:
            if fullhouse[2].count(wildcard) > carddict[wildcard]:
                to_remove.append(fullhouse)
        for fullhouse in to_remove:
            fullhouses.remove(fullhouse)

        return fullhouses


# 注意A可以作14也可以作1


    def get_all_straight(self, carddict, current_rank):   # 5张牌
        # 先将逢人配拿掉，再把逢人配加到每个级数组内，最后再把多的逢人配组合删掉
        # 将牌按照级数分类
        straights = []

        carddict1 = carddict.copy()
        wildcard = 'H'+current_rank
        wildcardnum = carddict1[wildcard]
        carddict1[wildcard] = 0
        rankdict = self.dict2rankdict(carddict1)
        for rank in rankdict:
            if rank not in ['SB', 'HR']:
                rankdict[rank] += [wildcard]*wildcardnum

        rank_has_enoughcard = [
            rank for rank in rankdict if len(rankdict[rank]) >= 1]
        if len(rank_has_enoughcard) >= 5:
            combinations = list(list(combination) for combination in itertools.combinations(
                rank_has_enoughcard, 5))

            straight_ranks = [
                combination for combination in combinations if self.is_consecutive(combination)]

            for straight_rank in straight_ranks:
                if '2' in straight_rank and 'A' in straight_rank:
                    rank = 1
                else:
                    rank = min(
                        rank2num[straight_rank[0]],
                        rank2num[straight_rank[1]],
                        rank2num[straight_rank[2]],
                        rank2num[straight_rank[3]],
                        rank2num[straight_rank[4]]
                    )
                for a in range(len(rankdict[straight_rank[0]])):
                    for b in range(len(rankdict[straight_rank[1]])):
                        for c in range(len(rankdict[straight_rank[2]])):
                            for d in range(len(rankdict[straight_rank[3]])):
                                for e in range(len(rankdict[straight_rank[4]])):
                                    straights.append(['Straight',
                                                      rank,
                                                      [rankdict[straight_rank[0]][a],
                                                       rankdict[straight_rank[1]][b],
                                                       rankdict[straight_rank[2]][c],
                                                       rankdict[straight_rank[3]][d],
                                                       rankdict[straight_rank[4]][e]]])

        to_remove = []
        for straight in straights:
            if straight[2].count(wildcard) > wildcardnum:
                to_remove.append(straight)
        for straight in to_remove:
            straights.remove(straight)

        return straights

    def get_all_bomb(self, carddict, current_rank):   # 4-8张牌
        # 先将逢人配拿掉，再把逢人配加到每个级数组内，最后再把多的逢人配组合删掉
        # 将牌按照级数分类
        bombs = []

        carddict1 = carddict.copy()
        wildcard = 'H'+current_rank
        wildcardnum = carddict1[wildcard]
        carddict1[wildcard] = 0
        rankdict = self.dict2rankdict(carddict1)
        for rank in rankdict:
            if rank not in ['SB', 'HR']:
                rankdict[rank] += [wildcard]*wildcardnum

        rank_has_enoughcard = [
            rank for rank in rankdict if len(rankdict[rank]) >= 4]

        for rank in rank_has_enoughcard:
            if rank == current_rank:
                ranknum = 15
            else:
                ranknum = rank2num[rank]
            for i in range(4, len(rankdict[rank])+1):
                if i <= 5:
                    for combination in itertools.combinations(rankdict[rank], i):
                        bombs.append(
                            ['Bomb', 440+(i-4)*20+ranknum, list(combination)])
                elif i >= 6:
                    for combination in itertools.combinations(rankdict[rank], i):
                        bombs.append(
                            ['Bomb', 500+(i-6)*20+ranknum, list(combination)])

        return bombs

    def get_all_tianwang(self, carddict):
        tianwang = []
        if carddict['SB'] == 2 and carddict['HR'] == 2:
            tianwang.append(['Bomb', 600, ['SB', 'SB', 'HR', 'HR']])

        return tianwang

    def get_all_straight_flush(self, carddict, current_rank):   # 5张牌
        flushs = []
        straights = self.get_all_straight(carddict, current_rank)
        wildcard = 'H'+current_rank
        for straight in straights:
            flush = straight.copy()
            straight = [card for card in straight[2] if card != wildcard]
            if all(card[0] == straight[0][0] for card in straight):
                flush[0] = 'StraightFlush'
                flush[1] += 480
                flushs.append(flush)

        return flushs

    def is_single(self, carddict):  # 1张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        return sum == 1

    def is_pair(self, carddict, current_rank):   # 2张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 2:
            pairs = self.get_all_pair(carddict, current_rank)
            if len(pairs) > 0:
                return True
        return False

    def is_triple(self, carddict, current_rank):   # 3张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 3:
            triples = self.get_all_triple(carddict, current_rank)
            if len(triples) > 0:
                return True
        return False

    def is_plate(self, carddict, current_rank):  # 6张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 6:   # 如果数目只有6张且正好能组成钢板，那就是钢板。
            plates = self.get_all_plate(carddict, current_rank)
            if len(plates) > 0:
                return True
        return False

    def is_tube(self, carddict, current_rank):   # 6张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 6:
            tubes = self.get_all_tube(carddict, current_rank)
            if len(tubes) > 0:
                return True
        return False

    def is_fullhouse(self, carddict, current_rank):   # 5张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 5:
            fullhouses = self.get_all_fullhouse(carddict, current_rank)
            if len(fullhouses) > 0:
                return True
        return False

    def is_straight(self, carddict, current_rank):   # 5张牌
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 5:
            straights = self.get_all_straight(carddict, current_rank)
            if len(straights) > 0:
                return True
        return False

    def is_bomb(self, carddict, current_rank):
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum >= 4:
            allbombcard = []
            wildcard = 'H'+current_rank
            for card in carddict:
                allbombcard += [card]*carddict[card]
                bombcard = [card for card in allbombcard if card != wildcard]
            if all(card[1] == bombcard[0][1] for card in bombcard):
                return True
        return False

    def is_flush(self, carddict, current_rank):
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 5:
            flushs = self.get_all_straight_flush(carddict, current_rank)
            if len(flushs) > 0:
                return True
        return False

    def is_tianwang(self, carddict):
        sum = 0
        for card in carddict:
            sum += carddict[card]
        if sum == 4:
            if carddict['SB'] == 2 and carddict['HR'] == 2:
                return True
        return False

    def get_value(self, carddict, current_rank):
        if self.is_tianwang(carddict):
            return 300
        elif self.is_flush(carddict, current_rank):
            flushs = self.get_all_straight_flush(carddict, current_rank)
            value = np.max([flush[1] for flush in flushs])
            return value
        elif self.is_bomb(carddict, current_rank):
            bombs = self.get_all_bomb(carddict, current_rank)
            value = np.max([bomb[1] for bomb in bombs])
            return value
        elif self.is_straight(carddict, current_rank):
            straights = self.get_all_straight(carddict, current_rank)
            value = np.max([straight[1] for straight in straights])
            return value
        elif self.is_fullhouse(carddict, current_rank):
            fullhouses = self.get_all_fullhouse(carddict, current_rank)
            value = np.max([fullhouse[1] for fullhouse in fullhouses])
            return value
        elif self.is_plate(carddict, current_rank):  # KKAA+2个逢人配怎么办
            plates = self.get_all_plate(carddict, current_rank)
            value = plates[0][1]
            return value
        elif self.is_tube(carddict, current_rank):
            tubes = self.get_all_tube(carddict, current_rank)
            value = np.max([tube[1] for tube in tubes])
            return value
        elif self.is_triple(carddict, current_rank):
            triples = self.get_all_triple(carddict, current_rank)
            value = triples[0][1]
            return value
        elif self.is_pair(carddict, current_rank):
            pairs = self.get_all_pair(carddict, current_rank)
            value = pairs[0][1]
            return value
        elif self.is_single(carddict):
            singles = self.get_all_single(carddict, current_rank)
            value = singles[0][1]
            return value
        elif carddict == None:
            return 0


# greatcard,handcard均为dict

    def get_actionlist(self, greatcard, handcard, current_rank):

        greatvalue = self.get_value(greatcard, current_rank)

        actionlist = []

        if self.is_tianwang(greatcard):
            actionlist.append(['PASS', 'PASS', 'PASS'])
            return actionlist

        elif self.is_flush(greatcard, current_rank) or self.is_bomb(greatcard, current_rank):
            actionlist.append(['PASS', 'PASS', 'PASS'])
            tianwang = self.get_all_tianwang(handcard)
            bombs = self.get_all_bomb(handcard, current_rank)
            flushs = self.get_all_straight_flush(handcard, current_rank)
            for flush in flushs:
                if flush[1] > greatvalue:
                    actionlist.append(flush)
            if len(tianwang) >= 1:
                actionlist.append(tianwang)
            for bomb in bombs:
                if bomb[1] > greatvalue:
                    actionlist.append(bomb)

        else:
            tianwang = self.get_all_tianwang(handcard)
            bombs = self.get_all_bomb(handcard, current_rank)
            flushs = self.get_all_straight_flush(handcard, current_rank)
            actionlist = actionlist + tianwang + bombs + flushs
            if self.is_straight(greatcard, current_rank):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                straights = self.get_all_straight(handcard, current_rank)
                for straight in straights:
                    if straight[1] > greatvalue:
                        actionlist.append(straight)
            elif self.is_fullhouse(greatcard, current_rank):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                fullhouses = self.get_all_fullhouse(handcard, current_rank)
                for fullhouse in fullhouses:
                    if fullhouse[1] > greatvalue:
                        actionlist.append(fullhouse)
            elif self.is_plate(greatcard, current_rank):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                plates = self.get_all_plate(handcard, current_rank)
                for plate in plates:
                    if plate[1] > greatvalue:
                        actionlist.append(plate)
            elif self.is_tube(greatcard, current_rank):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                tubes = self.get_all_tube(handcard, current_rank)
                for tube in tubes:
                    if tube[1] > greatvalue:
                        actionlist.append(tube)
            elif self.is_triple(greatcard, current_rank):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                triples = self.get_all_triple(handcard, current_rank)
                for triple in triples:
                    if triple[1] > greatvalue:
                        actionlist.append(triple)
            elif self.is_pair(greatcard, current_rank):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                pairs = self.get_all_pair(handcard, current_rank)
                for pair in pairs:
                    if pair[1] > greatvalue:
                        actionlist.append(pair)
            elif self.is_single(greatcard):
                actionlist.append(['PASS', 'PASS', 'PASS'])
                singles = self.get_all_single(handcard, current_rank)
                for single in singles:
                    if single[1] > greatvalue:
                        actionlist.append(single)
            else:
                singles = self.get_all_single(handcard, current_rank)
                pairs = self.get_all_pair(handcard, current_rank)
                triples = self.get_all_triple(handcard, current_rank)
                tubes = self.get_all_tube(handcard, current_rank)
                plates = self.get_all_plate(handcard, current_rank)
                fullhouses = self.get_all_fullhouse(handcard, current_rank)
                straights = self.get_all_straight(handcard, current_rank)
                actionlist = actionlist + singles + pairs + \
                    triples + tubes + plates + fullhouses + straights

        return actionlist

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def get(self, card):
        self.cardsInHand.append(card)

    def arrange(self, card_key):
        self.cardsInHand.sort(key=card_key)

    def playCards(self, game):
        # h = Hand(self.selectedCards)
        self.cardsPlayed = []
        while self.selectedCards != []:
            card = self.selectedCards[0]
            self.cardsPlayed.append(card)
            self.selectedCards.remove(card)
            self.cardsInHand.remove(card)
        game.cardsOnTable = self.cardsPlayed
        game.lastPlayer = self
        self.passed = False
        game.numTurns += 1
        for p in game.players:
            p.moves[game.players.index(self)].append(
                self.str2dict(self.list2str(self.cardsPlayed)))
            p.action_order.append(game.players.index(self))
            p.action_seq.append(self.cardsPlayed)
        if len(self.cardsInHand) == 0:
            self.isOver = True
            self.overTurn = game.numTurns
            self.ranking = game.nextRanking
            game.nextRanking += 1

    def passTurn(self, game):
        for card in self.selectedCards:
            card.isSelected = False
        self.selectedCards = []
        self.cardsPlayed = []
        self.passed = True
        game.numTurns += 1
        game.nextPlayer()
        for p in game.players:
            p.moves[game.players.index(self)].append(self.str2dict('PASS'))
            p.action_order.append(game.players.index(self))
            p.action_seq.append('PASS')

    def drawNumCardsLeft(self, screen, game):
        font = pygame.font.Font(None, 30)
        playerText = font.render(f"{self}", True, (255,) * 3)
        text = font.render(
            f"{len(self.cardsInHand)} cards left", True, (255,) * 3)
        index = game.players.index(self)
        if index == 0:
            startX, startY = WIDTH / 2 - 55, 720
        elif index == 1:
            startX, startY = 895, HEIGHT / 2 - 100
        elif index == 2:
            startX, startY = WIDTH / 2 - 55, 20
        else:
            startX, startY = 15, HEIGHT / 2 - 100
        screen.blit(playerText, (startX, startY))
        screen.blit(text, (startX, startY + 20))

    def drawCardsPlayed(self, screen, game):
        index = game.players.index(self)
        if index == 0:
            startX, startY = WIDTH / 2 - \
                ((len(self.cardsPlayed) - 1) * 20 + 105) / 2, 330
        elif index == 1:
            startX, startY = 690, HEIGHT/2 - 130
        elif index == 2:
            startX, startY = WIDTH/2 - \
                ((len(self.cardsPlayed) - 1) * 20 + 105) / 2, 130
        else:
            startX, startY = 150, HEIGHT/2 - 130
        for i in range(len(self.cardsPlayed)):
            card = self.cardsPlayed[i]
            screen.blit(card.image, (startX + 20 * i, startY))

    def drawPass(self, screen, game):
        font = pygame.font.Font(None, 30)
        index = game.players.index(self)
        if index == 0:
            startX, startY = WIDTH / 2 - \
                ((len(self.cardsPlayed) - 1) * 20 + 105) / 2, 450
        elif index == 1:
            startX, startY = 750, HEIGHT / 2 - 130
        elif index == 2:
            startX, startY = WIDTH / 2 - \
                ((len(self.cardsPlayed) - 1) * 20 + 105) / 2, 130
        else:
            startX, startY = 150, HEIGHT / 2 - 130
        passText = font.render('PASS', True, (191,) * 3)
        screen.blit(passText, (startX, startY))

    def drawCards(self, screen):
        startX = WIDTH / 2 - ((len(self.cardsInHand) - 1) * 20 + 105) / 2
        startY = 560
        for i in range(len(self.cardsInHand)):
            card = self.cardsInHand[i]
            if card.isSelected:
                screen.blit(card.image, (startX + 20 * i, startY - 20))
            else:
                screen.blit(card.image, (startX + 20 * i, startY))

    def select(self, game, event):
        if game.players.index(self) == 0:
            startX = WIDTH / 2 - ((len(self.cardsInHand) - 1) * 20 + 105) / 2
            startY = 560
            x, y = event.pos
            if startX < x < startX + 20 * (len(self.cardsInHand) - 1) + 105:
                i = -1 if x > startX + 20 * \
                    (len(self.cardsInHand) - 1) else int((x - startX) // 20)
                if self.cardsInHand[i].isSelected:
                    if startY - 20 < y < startY + 130:
                        self.cardsInHand[i].isSelected = False
                else:
                    if startY < y < startY + 160:
                        self.cardsInHand[i].isSelected = True
        else:
            self.AISelect(game)
        self.selectedCards = [
            card for card in self.cardsInHand if card.isSelected]

    def cal_remaincardNum(self, game):
        remaincardNum = [27, 27, 27, 27]

        if game.numTurns >= game.players[0].myPos + 1:
            cardnum = 0
            moves_p1 = self.moves[0]
            for move in moves_p1:
                if move == 'PASS':
                    cardnum += 0
                else:
                    cardnum += sum(move.values())
        else:
            cardnum = 0
        remaincardNum[0] = remaincardNum[0] - cardnum

        if game.numTurns >= game.players[1].myPos + 1:
            cardnum = 0
            moves_p2 = self.moves[1]
            for move in moves_p2:
                if move == 'PASS':
                    cardnum += 0
                else:
                    cardnum += sum(move.values())
        else:
            cardnum = 0
        remaincardNum[1] = remaincardNum[1] - cardnum

        if game.numTurns >= game.players[2].myPos + 1:
            cardnum = 0
            moves_p3 = self.moves[2]
            for move in moves_p3:
                if move == 'PASS':
                    cardnum += 0
                else:
                    cardnum += sum(move.values())
        else:
            cardnum = 0
        remaincardNum[2] = remaincardNum[2] - cardnum

        if game.numTurns >= game.players[3].myPos + 1:
            cardnum = 0
            moves_p4 = self.moves[3]
            for move in moves_p4:
                if move == 'PASS':
                    cardnum += 0
                else:
                    cardnum += sum(move.values())
        else:
            cardnum = 0
        remaincardNum[3] = remaincardNum[3] - cardnum

        self.remaincardNum = remaincardNum

    def cal_partner_array(self, game):
        teammate_moves = self.moves[game.players.index(self)-2]
        if teammate_moves == []:
            return -1*np.ones(54)
        elif self.remaincardNum[game.players.index(self)-2] == 0:
            return -1*np.ones(54)
        else:
            if teammate_moves[-1] == self.str2dict('PASS'):
                return np.zeros(54)
            else:
                return self.dict2array(teammate_moves[-1])

    # 按照下家、队友、上家记录
    def cal_playedcards(self, game):
        try:
            down_moves = self.moves[game.players.index(self)-3]
            down_playedcards = self.allcards()
            for move in down_moves:
                for card in down_playedcards.keys():
                    down_playedcards[card] += move[card]
        except:
            down_playedcards = self.allcards()

        try:
            teammate_moves = self.moves[game.players.index(self)-2]
            teammate_playedcards = self.allcards()
            for move in teammate_moves:
                for card in teammate_playedcards.keys():
                    teammate_playedcards[card] += move[card]
        except:
            teammate_playedcards = self.allcards()

        try:
            up_moves = self.moves[game.players.index(self)-1]
            up_playedcards = self.allcards()
            for move in up_moves:
                for card in up_playedcards.keys():
                    up_playedcards[card] += move[card]
        except:
            up_playedcards = self.allcards()

        self.playedcards = [down_playedcards,
                            teammate_playedcards, up_playedcards]

    def proc_universal(self):
        res = np.zeros(12, dtype=np.int8)
        cur_rank = int(rank2num[self.current_rank])-1
        if self.myHandCards['H'+self.current_rank] == 0:
            return res

        res[0] = 1
        rock_flag = 0
        handCards = self.dict2array(self.myHandCards)
        for i in range(4):
            left, right = 0, 5
            temp = [handCards[i + j*4] if i+j*4 !=
                    (cur_rank-1)*4 else 0 for j in range(5)]
            while right <= 12:
                zero_num = temp.count(0)
                if zero_num <= 1:
                    rock_flag = 1
                    break
                else:
                    temp.append(handCards[i + right*4]
                                if i+right*4 != (cur_rank-1)*4 else 0)
                    temp.pop(0)
                    left += 1
                    right += 1
            if rock_flag == 1:
                break
        res[1] = rock_flag

        num_count = [0] * 13
        for i in range(4):
            for j in range(13):
                if handCards[i + j*4] != 0 and i + j*4 != (cur_rank-1)*4:
                    num_count[j] += 1
        num_max = max(num_count)
        if num_max >= 6:
            res[2:8] = 1
        elif num_max == 5:
            res[3:8] = 1
        elif num_max == 4:
            res[4:8] = 1
        elif num_max == 3:
            res[5:8] = 1
        elif num_max == 2:
            res[6:8] = 1
        else:
            res[7] = 1
        temp = 0
        for i in range(13):
            if num_count[i] != 0:
                temp += 1
                if i >= 1:
                    if num_count[i] == 2 and num_count[i-1] >= 3 or num_count[i] >= 3 and num_count[i-1] == 2:
                        res[9] = 1
                    elif num_count[i] == 2 and num_count[i-1] == 2:
                        res[11] = 1
                if i >= 2:
                    if num_count[i-2] == 1 and num_count[i-1] >= 2 and num_count[i] >= 2 or \
                            num_count[i-2] >= 2 and num_count[i-1] == 1 and num_count[i] >= 2 or \
                            num_count[i-2] >= 2 and num_count[i-1] >= 2 and num_count[i] == 1:
                        res[10] = 1
            else:
                temp = 0
        if temp >= 4:
            res[8] = 1
        return res

    def BombInLeftCards(self, action):
        cardsleft = [str(card) for card in self.cardsInHand]
        
        for card in action[2]:
            if card in cardsleft:
                cardsleft.remove(card)
        
        # cardsleft = [str(card) for card in self.cardsInHand if str(card) not in action[2]]
        cardsleftdict = self.str2dict(self.list2str(cardsleft))
        # actionlistAfter = self.get_actionlist(
        #     self.str2dict('PASS'), cardsleftdict, self.current_rank)
        bombactions = self.get_all_bomb(cardsleftdict, self.current_rank)
        # BombListAfter = []
        # for action in actionlistAfter:
        #     if action[0] == 'Bomb':
        #         BombListAfter.append(action)
        if bombactions == []:
            return False
        else:
            return bombactions
        
    def StraightFlushInLeftCards(self, action):
        cardsleft = [str(card) for card in self.cardsInHand]
        
        for card in action[2]:
            if card in cardsleft:
                cardsleft.remove(card)
        
        # cardsleft = [str(card) for card in self.cardsInHand if str(card) not in action[2]]
        cardsleftdict = self.str2dict(self.list2str(cardsleft))
        # actionlistAfter = self.get_actionlist(
        #     self.str2dict('PASS'), cardsleftdict, self.current_rank)
        straighflushactions = self.get_all_straight_flush(cardsleftdict, self.current_rank)
        # StraighFlushListAfter = []
        # for action in actionlistAfter:
        #     if action[0] == 'StraightFlush':
        #         StraighFlushListAfter.append(action)
        if straighflushactions == []:
            return False
        else:
            return straighflushactions
    
    def WinInOneTurn(self,action):
        cardsleft = [str(card) for card in self.cardsInHand if str(card) not in action[2]]
        cardsleftdict = self.str2dict(self.list2str(cardsleft))
        if self.is_single(cardsleftdict):
            return tuple([1,'Single'])
        elif self.is_pair(cardsleftdict,self.current_rank):
            return tuple([1,'Pair'])
        elif self.is_triple(cardsleftdict,self.current_rank):
            return tuple([1,'Trips'])
        elif self.is_plate(cardsleftdict, self.current_rank):
            return tuple([1,'TwoTrips'])
        elif self.is_tube(cardsleftdict, self.current_rank):
            return tuple([1,'ThreePair'])
        elif self.is_fullhouse(cardsleftdict, self.current_rank):
            return tuple([1,'ThreeWithTwo'])
        elif self.is_straight(cardsleftdict, self.current_rank):
            return tuple([1,'Straight'])
        elif self.is_bomb(cardsleftdict, self.current_rank) or self.is_tianwang(cardsleftdict):
            return tuple([1,'Bomb'])
        elif self.is_flush(cardsleftdict, self.current_rank):
            return tuple([1,'StraightFlush'])
        else:
            try:
                if len(self.StraightFlushInLeftCards(action)) >= 1 or len(self.BombInLeftCards(action)) >= 1:
                    return tuple([2,None])
                else:
                    return tuple([0,None])
            except:
                return tuple([0,None])

    def current_situation(self, game):
        self.cal_remaincardNum(game)
        selfindex = game.players.index(self)
        opponents = [self.remaincardNum[selfindex-1],
                     self.remaincardNum[selfindex-3]]
        myself = len(self.cardsInHand)

        if opponents[0] == 0 and opponents[1] > 0:
            if opponents[1] >= STATE_NUM[0]:
                return 'start'
            elif opponents[1] >= STATE_NUM[1]:
                return 'middle'
            elif opponents[1] >= STATE_NUM[2]:
                return 'end'
            else:
                return 'almost over'
        elif opponents[1] == 0 and opponents[0] > 0:
            if opponents[0] >= STATE_NUM[0]:
                return 'start'
            elif opponents[0] >= STATE_NUM[1]:
                return 'middle'
            elif opponents[0] >= STATE_NUM[2]:
                return 'end'
            else:
                return 'almost over'
        else:
            if opponents[0] >= STATE_NUM[0] and opponents[1] >= STATE_NUM[0]:
                if myself < STATE_NUM[1]:
                    return 'middle'
                else:
                    return 'start'
            elif (opponents[0] < STATE_NUM[0] and opponents[0] >= STATE_NUM[1] and opponents[1] >= STATE_NUM[1]) or (opponents[1] < STATE_NUM[0] and opponents[1] >= STATE_NUM[1] and opponents[0] >= STATE_NUM[1]):
                if myself >= STATE_NUM[0]:
                    return 'start'
                else:
                    return 'middle'
            elif (opponents[0] >= STATE_NUM[2] or opponents[1] >= STATE_NUM[2]):
                return 'end'
            else:
                return 'almost over'

    def card_status(self):
        self.myHandCards = self.str2dict(self.list2str(self.cardsInHand))
        team = [self.myPos, (self.myPos + 2) % 4]
        opponents = [(self.myPos + 2) % 4, (self.myPos + 2) % 4]
        cal_num = 0
        length = 10
        if len(self.action_order) >= 7:
            for i in range(-7, 0):
                if self.action_order[i] in opponents and self.action_seq[i] != 'PASS':
                    length += len(self.action_seq[i])
                    cal_num += 1
                elif self.action_order[i] in team and self.action_seq[i] != 'PASS':
                    length = 10
                    cal_num = 0
        return max(1, cal_num), length * 0.13

    def penalty_for_bomb(self, game):
        selfindex = game.players.index(self)
        if game.lastPlayer == self:
            game.cardsOnTable = []
            self.greatcard = self.str2dict('PASS')
        elif game.lastPlayer == game.players[selfindex - 1] or \
                game.lastPlayer == game.players[selfindex - 3] or \
                game.lastPlayer == game.players[selfindex - 2]:
            self.greatcard = self.str2dict(self.list2str(game.cardsOnTable))
        else:
            self.greatcard = self.str2dict('PASS')
        self.myHandCards = self.str2dict(self.list2str(self.cardsInHand))
        actionlist = self.get_actionlist(
            self.greatcard, self.myHandCards, self.current_rank)
        add_weight, length = self.card_status()
        add_weight = add_weight * length
        single, pairs, straights = get_info_for_penalty(
            [str(card) for card in self.cardsInHand], self.current_rank)
        cards_in_straights = set(
            card for straight in straights for card in straight)
        # 找出在单张中但不在顺子中的牌
        unique_single_cards = []
        for card in single:
            if card not in cards_in_straights:
                unique_single_cards.append(card)
        # unique_single_cards = [
        #     card for card in single if card not in cards_in_straights]
        unique_pairs_cards = set(card[1:] for card in pairs)
        penalty_value = 3 + 1.8 * \
            len(unique_single_cards) + 1.8 * len(unique_pairs_cards)
        # 这里我们设定penalty_value < 7即为较好
        penalty_weight = math.log(penalty_value) / math.log(4)

        num_legal_actions = len(actionlist)
        situation = self.current_situation(game)
        penalty = [0] * num_legal_actions
        level_card = 'H'+self.current_rank
        
        opponents = [self.remaincardNum[(selfindex + 1) % 4],
                     self.remaincardNum[(selfindex + 3) % 4]]
        
        for i in range(num_legal_actions):
            action = actionlist[i]
            if action[0] != 'PASS':
                if action[0] == 'Bomb':
                    if situation == 'start':
                        if len(action[2]) == 4 and not ('HR' in action[2]):
                            penalty[i] -= (0.65 * penalty_weight) / add_weight
                        elif len(action[2]) == 4 and ('HR' in action[2]):
                            penalty[i] -= 1.0
                        else:
                            penalty[i] -= (0.75 * penalty_weight) / add_weight
                    elif situation == 'middle':
                        if len(action[2]) == 4 and ('HR' in action[2]):
                            penalty[i] -= (0.95 * penalty_weight) / add_weight
                        elif len(action[2]) == 4:
                            penalty[i] -= (0.45 * penalty_weight) / add_weight
                        else:
                            penalty[i] -= (0.65 * penalty_weight) / add_weight
                    elif situation == 'end':
                        if len(action[2]) == 4 and not ('HR' in action[2]):
                            penalty[i] += 0.20 
                        else:
                            penalty[i] += 0.05 
                    elif situation == 'almost over':
                        if len(action[2]) == 4 and not ('HR' in action[2]):
                            penalty[i] += 0.15
                        else:
                            penalty[i] += 0.35
                elif action[0] == 'StraightFlush':
                    if situation == 'start':
                        penalty[i] -= (1.5 * penalty_weight) / add_weight
                    elif situation == 'middle':
                        penalty[i] -= (0.75 * penalty_weight) / add_weight
                    elif situation == 'almost over':
                        penalty[i] += 0.65
                if len(action) == 3 and len(action[2]) > 0:
                    for card in action[2]:
                        if card == level_card:
                            if situation == 'start':
                                penalty[i] -= 0.75
                            elif situation == 'middle':
                                penalty[i] -= 0.25
                            elif situation == 'almost over':
                                penalty[i] += 0.35
                if game.lastPlayer == game.players[selfindex-2] and self.is_bomb(self.greatcard, self.current_rank):
                    if action[0] != 'PASS':
                        if len(self.cardsInHand) == len(action[2]):
                            penalty[i] += 0.3
                        elif len(self.cardsInHand) > len(action[2]):
                            penalty[i] -= 1
            else:
                #如果最大的是炸弹并且是对手出的 
                if self.is_bomb(self.greatcard, self.current_rank) and (game.lastPlayer == game.players[(selfindex + 1) % 4] or game.lastPlayer == game.players[(selfindex + 3) % 4]):
                    reward = 0.0
                    for j in range(num_legal_actions):
                        if i != j:
                            action = actionlist[j]
                            if action[0] == 'Bomb':
                                bombs = self.BombInLeftCards(action)
                                if bombs == False:
                                    if situation == 'start' or situation == 'middle':
                                        penalty[j] -= 1.5
                                        reward += 0.35
                                    elif situation == 'end':
                                        penalty[j] -= 0.75
                                        reward += 0.15
                                else:
                                    num_bomb = len(bombs)
                                    if situation == 'start' or situation == 'middle':
                                        penalty[j] -= max(1.0 - num_bomb * 0.34, 0.0)
                                        reward += 0.1
                                straightflushes = self.StraightFlushInLeftCards(action)
                                if straightflushes == False:
                                    if situation == 'start' or situation == 'middle':
                                        penalty[j] -= 2.5
                                        reward += 0.45
                                    elif situation == 'end':
                                        penalty[j] -= 0.85
                                        reward += 0.25
                                else:
                                    num_sf = len(straightflushes)
                                    if situation == 'start' or situation == 'middle':
                                        penalty[j] -= max(1.0 - num_sf * 0.25, 0.1)
                                        reward += 0.1
                    penalty[i] += min(reward, 1.5)
        return penalty

    def addition_for_action(self, game):
        useless_dict = {'2': 0.9, '3': 0.8, '4': 0.7, '5': 0.6,
                        '6': 0.5, '7': 0.4, '8': 0.3, '9': 0.2, 'T': 0.1}
        rank_card = 'H'+self.current_rank
        useful_list = [rank_card, 'SB', 'HR']
        next_best = ['J', 'Q', 'K', 'A', self.current_rank]
        add_weight, _ = self.card_status()
        self.myHandCards = self.str2dict(self.list2str(self.cardsInHand))
        actionlist = self.get_actionlist(
            self.greatcard, self.myHandCards, self.current_rank)
        num_legal_actions = len(actionlist)
        addition = [0] * num_legal_actions
        situation = self.current_situation(game)
        self.cal_remaincardNum(game)
        selfindex = game.players.index(self)
        opponents = [self.remaincardNum[selfindex-1],
                     self.remaincardNum[selfindex-3]]
        teammate = [self.remaincardNum[selfindex-2]]

        single, pairs, straights = get_info_for_penalty(
            [str(card) for card in self.cardsInHand], self.current_rank)
        
        #print(f"fuck single = {single}")

        for i in range(num_legal_actions):
            action = actionlist[i]
            if action[0] != 'PASS':
                if game.lastPlayer != None:
                    if game.lastPlayer == game.players[selfindex-2]:
                        addition[i] -= 0.45
                        if action[0] == 'Bomb' or action[0] == 'StraightFlush':
                            if len(self.cardsInHand) > len(action[2]):
                                addition[i] -= 1.5

                for j in range(0, 3):
                    if len(action[2]) == len([str(card) for card in self.cardsInHand]) - j:
                        addition[i] += (0.35 - 0.07 * j)

                if action[0] in ['Single'] and action[2][0] in pairs:
                    addition[i] -= 3
                if action[0] in ['Single'] and action[2][0][1] in useless_dict and action[2][0][1] != self.current_rank:
                    addition[i] += 0.15 * (1 + useless_dict[action[2][0][1]])

                if action[0] in ['Pair']:
                    card1 = action[2][0]
                    if card1 not in pairs:
                        addition[i] -= 2
                    elif action[0] in ['Pair'] and action[2][0][1] in useless_dict and action[2][0][1] != self.current_rank:
                        addition[i] += 0.18 * \
                            (1 + useless_dict[action[2][0][1]])

                for j in range(0, 3):
                    if action[0] in ['ThreeWithTwo'] and useful_list[j] in action[2]:
                        addition[i] -= 3.5
                if action[0] in ['ThreeWithTwo']:
                    two_attach = find_element_occurred_twice(action[2])
                    if two_attach in next_best:
                        addition[i] -= 0.5

                # 打配合让队友走
                if teammate == 1 and action[0] == 'Single' and action[2][0][1] in useless_dict and action[2][0][1] != self.current_rank:
                    addition[i] += 1.0 * add_weight * \
                        (1 + useless_dict[action[2][0][1]])
                elif teammate == 2 and (action[0] in ['Single', 'Pair']):
                    addition[i] += 0.4 * add_weight
                elif teammate == 3 and (action[0] in ['Single', 'Pair', 'Trips']):
                    addition[i] += 0.2 * add_weight
                
                if action[0] == 'Single':
                    if action[2][0] in single:
                        if situation == 'start':
                            addition[i] += 0.3
                    
                if game.lastPlayer == None or game.players.index(game.lastPlayer) == self.myPos:
                    if action[0] in ['Straight', 'ThreePair', 'ThreeWithTwo', 'TwoTrips']:
                        if situation == 'start':
                            addition[i] += (len(action[2]) - 3) * 0.2
                        elif situation == 'middle':
                            addition[i] += (len(action[2]) - 3) * 0.1
                        elif situation == 'end':
                            addition[i] += (len(action[2]) - 3) * 0.05
                        else:
                            addition[i] += (len(action[2]) - 3) * 0.15
                    elif action[0] == 'Single' and action[2][0] in single:
                        in_straight = False
                        for card in straights:
                            if action[2][0] == card:
                                in_straight = True
                                break
                        if not in_straight:
                            if situation == 'start':
                                addition[i] += 0.1
                            elif situation == 'middle':
                                addition[i] += 0.05
                            elif situation == 'end':
                                addition[i] += 0.15
                            else:
                                addition[i] += 0.02

                for opponent in opponents:
                    if opponent == 1 and action[0] != 'Single':
                        addition[i] += 1.0 * add_weight
                    if opponent == 1 and len(self.action_seq[-1]) == 1 and action[0] == 'Single':
                        if action[2][0] == 'HR':
                            addition[i] += 2
                        elif action[2][0] == 'SB':
                            addition[i] += 1
                    if opponent == 2 and not (action[0] in ['Single', 'Pair']):
                        addition[i] += 0.2 * add_weight
                    if opponent == 2 and (action[2] in [['SB', 'SB'], ['HR', 'HR']]):
                        addition[i] += 0.2 * add_weight
                    elif opponent == 3 and not (action[0] in ['Single', 'Pair', 'Trips']):
                        addition[i] += 0.2 * add_weight
                    elif opponent == 4 and not (action[0] in ['Single', 'Pair', 'Trips']):
                        addition[i] += 0.2 * add_weight
                        if (action[0] == 'Bomb' and len(action[2]) >= 4 or action[0] == 'StraightFlush'):
                            addition[i] += 0.2
                    elif opponent == 5 and not (action[0] in ['Single', 'Pair', 'Trips', 'Straight', 'ThreeWithTwo']) \
                            or (action[0] == 'Bomb' and len(action[2]) >= 5 or (len(action[2]) == 4 and 'SB' in action[2])) \
                            or (action[0] == 'StraightFlush'):
                        addition[i] += 0.2
                
                if len(self.cardsInHand) <= 16:
                    #before_bombs = self.get_all_bomb(self.str2dict(self.list2str(self.myHandCards)), self.current_rank)
                    bombs = self.BombInLeftCards(action)
                    #before_straightflushes = self.get_all_straight_flush(self.str2dict(self.list2str(self.myHandCards)), self.current_rank)
                    straightflushes = self.StraightFlushInLeftCards(action)
                    
                    if action[0] not in ['Bomb', 'StraightFlush']:
                        if bombs != False:
                            if situation == 'start' or situation == 'middle':
                                addition[i] += 0.25
                            elif situation == 'end':
                                addition[i] += 0.5
                            elif situation == 'almost over':
                                addition[i] += 1.0
                
                    if action[0] not in ['Bomb', 'StraightFlush']:
                        if straightflushes != False:
                            if situation == 'start' or situation == 'middle':
                                addition[i] += 0.3
                            elif situation == 'end':
                                addition[i] += 0.6
                            elif situation == 'almost over':
                                addition[i] += 1.2
                
                if len(self.cardsInHand) <= 9:
                    result = self.WinInOneTurn(action)
                    bombs = self.get_all_bomb(self.str2dict(self.list2str(self.myHandCards)), self.current_rank)
                    if result[0] == 0 and len(bombs) > 0:
                        addition[i] -= 1.0
                    elif result[0] == 2:
                        addition[i] += 0.5
                    elif result[0] == 1:
                        if result[1] in ['Bomb', 'StraightFlush']:
                            addition[i] += 2.5
                        elif result[1] in ['Straight', 'ThreeWithTwo', 'TwoTrips', 'ThreePair']:
                            addition[i] += 1.0
                        elif result[1] in ['Pair', 'Trips']:
                            addition[i] += 0.5
            else:
                if situation == 'end':
                    addition[i] -= 1.0
                elif situation == 'almost over':
                    addition[i] -= 2.0
                        
            bomb_size = None
            if action[0] == 'Bomb':
                bomb_size = len(action[2])
            elif action[0] == 'StraightFlush':
                bomb_size = 5
            level_score = get_score_by_situation(
                situation, self.current_rank, action[0], bomb_size)
            if level_score == 0:
                pass
            elif action[1] in level_score:
                addition[i] += level_score[action[1]]
            elif action[2][0][1] in level_score:
                addition[i] += level_score[action[2][0][1]]
        return addition

    def choose_best_action(self, game):

        self.myHandCards = self.str2dict(self.list2str(self.cardsInHand))
        actionlist = self.get_actionlist(
            self.greatcard, self.myHandCards, self.current_rank)
        handcard_array = self.dict2array(self.myHandCards)
        self.remainingcard = self.cal_remainingcard()
        remainingcard_array = self.dict2array(self.cal_remainingcard())
        greatcard_array = self.dict2array(self.greatcard)
        partner_array = self.cal_partner_array(game)
        remainnum_array = np.array([])
        self.cal_remaincardNum(game)
        selfindex = game.players.index(self)
        indexlist = [selfindex-3, selfindex-2, selfindex-1]
        for index in indexlist:
            num = self.remaincardNum[index]
            remain = self._get_one_hot_array(num, 27, 1)
            remainnum_array = np.concatenate((remainnum_array, remain), axis=0)
        playedcard_array = np.array([])
        self.cal_playedcards(game)
        for playedcard in self.playedcards:
            played_array = self.dict2array(playedcard)
            playedcard_array = np.concatenate(
                (playedcard_array, played_array), axis=0)
        ourcurrent = self._get_one_hot_array(
            rank2num[self.current_rank], 13, 0)
        oppcurrent = self._get_one_hot_array(
            rank2num[game.players[game.players.index(self)-1].current_rank], 13, 0)
        wildcurrent = self._get_one_hot_array(
            game.wildRank, 13, 0)
        universal_card_flag = self.proc_universal()

        penaltys = self.penalty_for_bomb(game)
        additions = self.addition_for_action(game)
        scores = []
        for i, actioninfo in enumerate(actionlist):
            penalty = penaltys[i]
            addition = additions[i]
            action = actioninfo[2]
            action_array = self.dict2array(
                self.str2dict(self.list2str(action)))
            x = np.hstack((handcard_array,
                           universal_card_flag,
                           remainingcard_array,
                           greatcard_array,
                           partner_array,
                           playedcard_array,
                           remainnum_array,
                           ourcurrent,
                           oppcurrent,
                           wildcurrent,
                           action_array
                           ))
            X = x.reshape((1, 567))
            score = self.model(X) + penalty + addition
            # if sum(self.greatcard.values()) == 0 and i == 0:
            #     score += -1000
            scores.append(score)
        index = scores.index(np.max(scores))
        best_action = actionlist[index]

        return best_action

    def AISelect(self, game):
        if game.lastPlayer == self:
            game.cardsOnTable = []
            self.greatcard = self.str2dict('PASS')
        elif game.lastPlayer == game.players[game.players.index(self) - 1] or \
                game.lastPlayer == game.players[game.players.index(self) - 3] or \
                game.lastPlayer == game.players[game.players.index(self) - 2]:
            self.greatcard = self.str2dict(self.list2str(game.cardsOnTable))
        else:
            self.greatcard = self.str2dict('PASS')
        self.myHandCards = self.str2dict(self.list2str(self.cardsInHand))
        best_action = self.choose_best_action(game)
        print('***********************************************************************')
        print('last player: ')
        print(game.lastPlayer)
        print(str(self)+' great card: ')
        greatcardstr = ''
        for card in self.greatcard:
            greatcardstr += card*self.greatcard[card]
        print(greatcardstr)
        print(str(self)+' best action:')
        print(best_action)
        for action in best_action[2]:
            for card in self.cardsInHand:
                if str(card) == action and card.isSelected == False:
                    card.isSelected = True
                    # print(card)
                    break
