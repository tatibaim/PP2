#Imports
import pygame, sys
from pygame.locals import *
import random, time
 
#Initialzing 
pygame.init()
 
#Setting up FPS 
FPS = 60
FramePerSec = pygame.time.Clock()
 
#Creating colors
BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
 
#Other Variables for use in the program
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 5
MONEY_SCORE = 0
next_speed = 10
 
moneta=pygame.image.load("Practice 11/racer upgrade/image/money.png")
gold_coin=pygame.image.load("Practice 11/racer upgrade/image/golden_coin.png")
silver_coin=pygame.image.load("Practice 11/racer upgrade/image/silver_coin.png")
bronze_coin=pygame.image.load("Practice 11/racer upgrade/image/bronze_coin.png")

#Setting up Fonts
font = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
game_over = font.render("Game Over", True, BLACK)
 
background = pygame.image.load("Practice 11/racer upgrade/image/AnimatedStreet.png")
 
#Create a white screen 
DISPLAYSURF = pygame.display.set_mode((400,600))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Racer")

icon = pygame.image.load("Practice 11/racer upgrade/image/icon.png")
pygame.display.set_icon(icon)
 
class Coin(pygame.sprite.Sprite):
      def __init__(self):
        super().__init__() 
        self.types = [
            {"image": pygame.image.load("Practice 11/racer upgrade/image/bronze_coin.png"), "value": 1},
            {"image": pygame.image.load("Practice 11/racer upgrade/image/silver_coin.png"), "value": 2},
            {"image": pygame.image.load("Practice 11/racer upgrade/image/golden_coin.png"), "value": 3}
        ]
        current_type = random.choice(self.types)
        self.image = current_type["image"]
        self.value = current_type["value"]
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(40, SCREEN_WIDTH-40), 0)  
 
      def move(self):
        self.rect.move_ip(0,SPEED)
        if (self.rect.top > 600):
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)
            self.image = random.choice(self.types)
            current_type = random.choice(self.types)
            self.image = current_type["image"]
            self.value = current_type["value"]
            
class Enemy(pygame.sprite.Sprite):
      def __init__(self):
        super().__init__() 
        self.image = pygame.image.load("Practice 11/racer upgrade/image/Enemy.png")
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(40, SCREEN_WIDTH-40), 0)  
 
      def move(self):
        self.rect.move_ip(0,SPEED)
        if (self.rect.top > 600):
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)
 
 
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__() 
        self.image = pygame.image.load("Practice 11/racer upgrade/image/Player.png")
        self.rect = self.image.get_rect()
        self.rect.center = (160, 520)
        
    def move(self):
        pressed_keys = pygame.key.get_pressed()
       #if pressed_keys[K_UP]:
            #self.rect.move_ip(0, -5)
       #if pressed_keys[K_DOWN]:
            #self.rect.move_ip(0,5)
         
        if self.rect.left > 0:
              if pressed_keys[K_LEFT]:
                  self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH:        
              if pressed_keys[K_RIGHT]:
                  self.rect.move_ip(5, 0)
                   
#Setting up Sprites        
P1 = Player()
E1 = Enemy()
M1 = Coin()
 
#Creating Sprites Groups
enemies = pygame.sprite.Group()
enemies.add(E1)

money = pygame.sprite.Group()
money.add(M1)

all_sprites = pygame.sprite.Group()
all_sprites.add(P1)
all_sprites.add(E1)
all_sprites.add(M1)
 
#Adding a new User event 
INC_SPEED = pygame.USEREVENT + 1
pygame.time.set_timer(INC_SPEED, 1000)

bgsound = pygame.mixer.Sound("Practice 11/racer upgrade/sound/background.wav")
bgsound.play()
#Game Loop
while True:
       
    #Cycles through all events occurring  
    for event in pygame.event.get():
        if MONEY_SCORE >= next_speed:
              SPEED += 3
              next_speed += 10
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
 
    DISPLAYSURF.blit(background, (0,0))
    
 
    #Moves and Re-draws all Sprites
    for entity in all_sprites:
        DISPLAYSURF.blit(entity.image, entity.rect)
        entity.move()
 
    #To be run if collision occurs between Player and Enemy
    if pygame.sprite.spritecollideany(P1, enemies):
        bgsound.stop()
        pygame.mixer.Sound('Practice 11/racer upgrade/sound/crash.wav').play()
        time.sleep(0.5)
            
            
        waiting = True
        while waiting:       
            DISPLAYSURF.fill(RED)
            DISPLAYSURF.blit(game_over, (30,250))
            score=font_small.render(f"Score: {MONEY_SCORE}", True, BLACK)
            DISPLAYSURF.blit(score, (150,325))
            restart_text=font_small.render("R-restart", True, BLACK)
            DISPLAYSURF.blit(restart_text, (150,500))
            quit_text=font_small.render("Q-quit", True, BLACK)
            DISPLAYSURF.blit(quit_text, (150,525))
           
            pygame.display.update()
            
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                        MONEY_SCORE = 0
                        SPEED = 5
                        E1.rect.top = 0
                        E1.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)
                        M1.rect.top = 0
                        M1.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)
                        bgsound.play()
                    if event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
    DISPLAYSURF.blit(bronze_coin, (5,40))
    DISPLAYSURF.blit(silver_coin, (5,70))
    DISPLAYSURF.blit(gold_coin, (5,100))  
    
    bronze_text = font_small.render("1", True, BLACK)
    silver_text = font_small.render("2", True, BLACK)
    gold_text = font_small.render("3", True, BLACK)     
    
    DISPLAYSURF.blit(bronze_text, (30,40))
    DISPLAYSURF.blit(silver_text, (30,70))
    DISPLAYSURF.blit(gold_text, (30,100))
                   
         
    scores_money = font_small.render(str(MONEY_SCORE), True, YELLOW)
    DISPLAYSURF.blit(scores_money, (10, 10))
    
    
    if pygame.sprite.spritecollideany(P1, money):
            pygame.mixer.Sound('Practice 11/racer upgrade/sound/lost_money.wav').play()
            MONEY_SCORE += M1.value
            M1.rect.top = 0
            M1.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)
            
            current_type = random.choice(M1.types)
            M1.image = current_type["image"]
            M1.value = current_type["value"]
    
    pygame.display.update()
    FramePerSec.tick(FPS)