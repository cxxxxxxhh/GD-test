import pygame
from CardGame import *

# !!!!!!!!!!!!!!!!!!!!!!!!!!!
# Citations:
# Introduction and Rules of Guan Dan: https://www.pagat.com/climbing/guan_dan.html
# Background images: http://www.dreamtemplate.com/dreamcodes/documentation/background_images.html
#                    https://www.scroogetheboardgame.co.uk/contact-us
#                    https://www.photohdx.com/pic-472/vintage-red-damask-floral-pattern-canvas-background
# Images of cards: http://www.bkill.com/download/176402.html#soft-downUrl
# !!!!!!!!!!!!!!!!!!!!!!!!!!!


def main():
    FPS = 20
    pygame.init()
    clock = pygame.time.Clock()
    g = Game(2, 2)
    p1, p2, p3, p4 = Player("Player 1"), Player("Player 2"), Player("Player 3"), Player("Player 4")
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
                #pygame.event.set_blocked(pygame.MOUSEWHEEL)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.offlineModeButton.collidepoint(event.pos):
                        g.startPage = False
                        g.offlineMode = True
                        g.newRound()
                    elif g.infoButton.collidepoint(event.pos):
                        g.startPage = False
                        g.infoPage = True
                    elif g.settingsButton.collidepoint(event.pos):
                        g.startPage = False
                        g.settingsPage = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            
            if g.settingsPage:
                mousePos = pygame.mouse.get_pos()
                g.drawSettingsPage(mousePos)
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
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
                        g.bg = "bg4.png"
                    with open("settings.txt", "w") as f:
                        f.write(f"{g.AISpeed} {g.bg}")
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                # pygame.display.update()
            if g.infoPage:
                g.drawInfoPage()
                #pygame.display.update()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
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
                # pygame.display.update()
            if g.introPage:
                g.drawIntroPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.backButton.collidepoint(event.pos):
                        g.introPage = False
                        g.infoPage = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                #pygame.display.update()
            if g.rulesPage:#!!!!!!!!!!!!!!!!!!!!!
                g.drawRulesPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.backButton.collidepoint(event.pos):
                        g.rulesPage = False
                        g.infoPage = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                #pygame.display.update()
            if g.thePlayPage:
                g.drawThePlayPage()
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.backButton.collidepoint(event.pos):
                        g.thePlayPage = False
                        g.infoPage = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                #pygame.display.update()
            if g.endPage:
                g.drawEndPage(g)
                pygame.display.update()
                event = pygame.event.wait()
                pygame.event.set_blocked(pygame.MOUSEMOTION)
                #for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.continueButton.collidepoint(event.pos):
                        g.endPage = False
                        g.newRound()
                        g.offlineMode = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                #pygame.display.update()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        #pygame.display.set_caption("Guan Dan 掼蛋")

        timer = 0
        while g.offlineMode:
            playersLeft = [player for player in g.players if not player.isOver]
            if len(playersLeft) == 1:
                playersLeft[0].ranking = g.nextRanking
                g.offlineMode = False
                g.endPage = True
                g.updateResult()
            if len(playersLeft) == 2 and g.players[g.players.index(playersLeft[0]) - 2] == playersLeft[1]:
                playersLeft[0].ranking = g.nextRanking
                g.nextRanking += 1
                playersLeft[1].ranking = g.nextRanking
                g.offlineMode = False
                g.endPage = True
                g.updateResult()

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
            if g.turn != g.players[0]:
                dt = clock.tick(FPS)
                timer += dt
                g.turn.select(g, event)
                if timer >= g.AISpeed:
                    if g.turn.selectedCards == []:
                        g.turn.passTurn(g)
                    else:
                        g.turn.playCards(g)
                        g.nextPlayer()
                    timer = 0
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if g.backButton.collidepoint(event.pos):
                        g.offlineMode = False
                        g.startPage = True
                    if g.turn == g.players[0]:
                        p1.select(g, event)
                        # font = pygame.font.Font(None, 24)
                        # g.clock=pygame.draw.circle(center=(WIDTH/2-230,500),radius=10)
                        # clockText=font.render(f"{elapsed_time_str}",True,(255,130,0))
                        # start_time = time.time()
                        #g.drawclock(screen,mousePos,g)!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # start_time = time.time()
                        if g.hintButton.collidepoint(event.pos):
                            p1.AISelect(g)
                        if g.deseletButton.collidepoint(event.pos):
                            for card in p1.cardsInHand:
                                card.isSelected = False
                        if g.playButton.collidepoint(event.pos):
                            # end_time = time.time()
                            # elapsed_time = end_time - start_time
                            # elapsed_time_str = "Elapsed Time: {:.2f} s".format(elapsed_time)
                            h = Hand(p1.selectedCards)
                            if g.lastPlayer == p1:
                                g.cardsOnTable = []
                            if h.isValid(g):
                                p1.playCards(g)
                                g.nextPlayer()
                            else:
                                for card in p1.selectedCards:
                                    card.isSelected = False
                                p1.selectedCards = []
                        # pass
                        if g.passButton.collidepoint(event.pos):
                            # end_time = time.time()
                            # elapsed_time = end_time - start_time
                            # elapsed_time_str = "Elapsed Time: {:.2f} s".format(elapsed_time)
                            if g.lastPlayer != g.players[0] and g.lastPlayer != None:
                                g.turn.passTurn(g)
                        # screen.blit(clockText,(WIDTH/2-230,507))

                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            pygame.display.update()
            clock.tick(FPS)


if __name__ == "__main__":
    main()

