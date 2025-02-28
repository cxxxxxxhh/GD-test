import pygame
from CardGame import *
import random

# !!!!!!!!!!!!!!!!!!!!!!!!!!!
# Citations:
# Introduction and Rules of Guan Dan: https://www.pagat.com/climbing/guan_dan.html
# Background images: http://www.dreamtemplate.com/dreamcodes/documentation/background_images.html
#                    https://www.scroogetheboardgame.co.uk/contact-us
#                    https://www.photohdx.com/pic-472/vintage-red-damask-floral-pattern-canvas-background
# Images of cards: http://www.bkill.com/download/176402.html#soft-downUrl
# !!!!!!!!!!!!!!!!!!!!!!!!!!!


def main():
    FPS = 30
    pygame.init()
    clock = pygame.time.Clock()
    g = Game(2, 2)
    p1, p2, p3, p4 = Player("Player 1",g), Player("Player 2",g), Player("Player 3",g), Player("Player 4",g)
    g.players += [p1, p2, p3, p4]
    g.setAISpeed()
    g.setBg()
    playing = True
    while playing:
        while not g.offlineMode:
            if g.startPage:
                g.drawStartPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.offlineModeButton.collidepoint(event.pos):
                            g.startPage = False
                            g.offlineMode = True
                            g.newRound()
                            for p in g.players:
                                p.get_myPos(g)
                                p.get_currentRank(g)
                        elif g.infoButton.collidepoint(event.pos):
                            g.startPage = False
                            g.infoPage = True
                        elif g.settingsButton.collidepoint(event.pos):
                            g.startPage = False
                            g.settingsPage = True
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
            if g.settingsPage:
                mousePos = pygame.mouse.get_pos()
                g.drawSettingsPage(mousePos)
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.backButton.collidepoint(event.pos):
                            g.settingsPage = False
                            g.startPage = True
                        if g.speed1Button.collidepoint(event.pos):
                            g.AISpeed = 300
                        if g.speed2Button.collidepoint(event.pos):
                            g.AISpeed = 500
                        if g.speed3Button.collidepoint(event.pos):
                            g.AISpeed = 1100
                        if g.bg1Button.collidepoint(event.pos):
                            g.bg = "bg1.png"
                        if g.bg2Button.collidepoint(event.pos):
                            g.bg = "bg2.jpg"
                        if g.bg3Button.collidepoint(event.pos):
                            g.bg = "bg3.jpg"
                        with open("settings.txt", "w") as f:
                            f.write(f"{g.AISpeed} {g.bg}")
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
            if g.infoPage:
                g.drawInfoPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.backButton.collidepoint(event.pos):
                            g.infoPage = False
                            g.startPage = True
                        if g.introButton.collidepoint(event.pos):
                            g.infoPage = False
                            g.introPage = True
                        if g.rulesButton.collidepoint(event.pos):
                            g.infoPage = False
                            g.rulesPage = True
                        if g.thePlayButton.collidepoint(event.pos):
                            g.infoPage = False
                            g.thePlayPage = True
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
            if g.introPage:
                g.drawIntroPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.backButton.collidepoint(event.pos):
                            g.introPage = False
                            g.infoPage = True
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
            if g.rulesPage:
                g.drawRulesPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                #for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.backButton.collidepoint(event.pos):
                            g.rulesPage = False
                            g.infoPage = True
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
            if g.thePlayPage:
                g.drawThePlayPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.backButton.collidepoint(event.pos):
                            g.thePlayPage = False
                            g.infoPage = True
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
            if g.endPage:
                g.drawEndPage(g)
                #g.updateResult()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)                
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if g.continueButton.collidepoint(event.pos):
                            g.endPage = False
                            g.newRound()
                            for p in g.players:
                                p.get_myPos(g)
                                p.get_currentRank(g)
                            g.offlineMode = True
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()
                pygame.display.update()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Guan Dan 掼蛋")

        timer = 0
        while g.offlineMode:
            
            playersLeft = [player for player in g.players if not player.isOver]
            # print(g.turn)
            if len(playersLeft) == 1:
                playersLeft[0].ranking = g.nextRanking
                g.offlineMode = False
                g.updateResult()
                g.endPage = True
                
            if len(playersLeft) == 2 and g.players[g.players.index(playersLeft[0]) - 2] == playersLeft[1]:
                playersLeft[0].ranking = g.nextRanking
                g.nextRanking += 1
                playersLeft[1].ranking = g.nextRanking
                g.offlineMode = False
                g.updateResult()
                g.endPage = True
                
            mousePos = pygame.mouse.get_pos()
            g.drawBasics(screen, mousePos, g)
            p1.drawCards(screen)

            for p in g.players:
                if not p.isOver:
                    p.drawCardsPlayed(screen, g)
                    p.drawNumCardsLeft(screen, g)
                    if p.passed:
                        p.drawPass(screen, g)
                else:
                    if g.numTurns < p.overTurn + len(playersLeft):
                        p.drawCardsPlayed(screen, g)
                    else:
                        if g.lastPlayer == p:
                            g.cardsOnTable = []
                            g.turn = g.players[g.players.index(p) - 2]
            # print(g.lastPlayer)
            if g.turn != g.players[0]:
                dt = clock.tick(FPS)
                timer += dt
                # g.turn.select(g, event)
                # print(1)
                if timer >= g.AISpeed:
                    
                    g.turn.select(g, event)
                    if g.turn.selectedCards == []:
                        g.turn.passTurn(g)
                    else:
                        g.turn.playCards(g)
                        g.nextPlayer()
                    timer = 0
                    # print([p1.ranking,p3.ranking])
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.backButton.collidepoint(event.pos):
                        g.offlineMode = False
                        g.startPage = True
                    if g.turn == g.players[0]:
                        p1.select(g, event)
                        # play
                        if g.hintButton.collidepoint(event.pos):
                            p1.AISelect(g)
                        if g.deseletButton.collidepoint(event.pos):
                            for card in p1.cardsInHand:
                                card.isSelected = False
                        if g.playButton.collidepoint(event.pos):
                            selectedCardsStr = p1.list2str(p1.selectedCards)
                            selectedCardsDict = p1.str2dict(selectedCardsStr)
                            if g.lastPlayer == p1:
                                g.cardsOnTable = []
                                p1.greatcard = p1.str2dict('Pass')        
                            elif g.lastPlayer == g.players[g.players.index(p1) - 1] or \
                                g.lastPlayer == g.players[g.players.index(p1) - 3] or \
                                g.lastPlayer == g.players[g.players.index(p1) - 2]:
                                p1.greatcard = p1.str2dict(p1.list2str(g.cardsOnTable))
                            else:
                                p1.greatcard = p1.str2dict('Pass')
                            p1.myHandCards = p1.str2dict(p1.list2str(p1.cardsInHand))
                            actionlist = p1.get_actionlist(p1.greatcard,p1.myHandCards,p1.current_rank)
                            factor = False
                            for action in actionlist:
                                actiondict = p1.str2dict(p1.list2str(action[2]))
                                if actiondict == selectedCardsDict:
                                    factor = True
                                    break
                                # else:
                                #     print(selectedCardsStr + ', '+p1.list2str(action[2])+' are not the same')
                            if factor:
                                p1.playCards(g)
                                g.nextPlayer()
                            else:
                                for card in p1.selectedCards:
                                    card.isSelected = False
                                p1.selectedCards = []
                        # pass
                        if g.passButton.collidepoint(event.pos):
                            if g.lastPlayer != g.players[0] and g.lastPlayer != None:
                                g.turn.passTurn(g)
                        # print([p1.ranking,p3.ranking])

                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            pygame.display.update()
            clock.tick(FPS)


if __name__ == "__main__":
    main()

