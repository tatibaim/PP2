# importing libraries
import pygame
import random

snake_speed = 15
level = 1

# Window size
window_x = 720
window_y = 480

# defining colors
black = pygame.Color(0, 0, 0)
white = pygame.Color(255, 255, 255)
red = pygame.Color(255, 0, 0)
green = pygame.Color(0, 255, 0)
blue = pygame.Color(0, 0, 255)

# Initialising pygame
pygame.init()

# Initialise game window
pygame.display.set_caption('Snake Game')
game_window = pygame.display.set_mode((window_x, window_y))

# FPS (frames per second) controller
fps = pygame.time.Clock()

def reset_game():
    global snake_position, snake_body, fruit_position
    global fruit_spawn, direction, change_to, score
    global level, snake_speed
    
    # defining snake default position
    snake_position = [100, 50]

    # defining first 4 blocks of snake body
    snake_body = [[100, 50],
                  [90, 50],
                  [80, 50],
                  [70, 50]
                  ]

    # fruit position --------------------------------------------------
    fruit_position = [random.randrange(1, (window_x//10)) * 10,
                      random.randrange(1, (window_y//10)) * 10]

    fruit_spawn = True

    # setting default snake direction towards right
    direction = 'RIGHT'
    change_to = direction

    # initial score
    score = 0
    level = 1
    snake_speed = 15


reset_game()

# displaying Score function
def show_score(choice, color, font, size):
  
    # creating font object score_font
    score_font = pygame.font.SysFont(font, size)
    
    # create the display surface object 
    # score_surface
    score_surface = score_font.render('Score : ' + str(score), True, color)
    
    # create a rectangular object for the text
    # surface object
    score_rect = score_surface.get_rect()
    
    # displaying text
    game_window.blit(score_surface, score_rect)
    
    level_font = pygame.font.SysFont(font, size)
    level_surface = level_font.render('Level : ' + str(level), True, color) #-----------------------------
    game_window.blit(level_surface, (1, 18))
    

# game over function
def game_over():
    
    # creating font object my_font
    my_font = pygame.font.SysFont('times new roman', 50)
    restart_font = pygame.font.SysFont('times new roman', 25)
    
    # creating a text surface on which text 
    # will be drawn
    game_over_surface = my_font.render(
        'Your Score is : ' + str(score), True, red)
    restart_surface = restart_font.render(
        'Press R to restart or Q to quit', True, white)

    game_over_surface_level= my_font.render(
        'Your Level is : ' + str(level), True, red) #-----------------------------
    
    
    # create a rectangular object for the text 
    # surface object
    game_over_rect = game_over_surface.get_rect()
    restart_rect = restart_surface.get_rect()
    game_over_surface_level_rect = game_over_surface_level.get_rect()
    # setting position of the text
    game_over_rect.midtop = (360, 120)
    restart_rect.midtop = (360, 240)
    game_over_surface_level_rect.midtop = (360, 160) #-----------------------------

    while True:
        game_window.fill(black)
        game_window.blit(game_over_surface, game_over_rect)
        game_window.blit(restart_surface, restart_rect)
        game_window.blit(game_over_surface_level, game_over_surface_level_rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    return
                if event.key == pygame.K_q:
                    pygame.quit()
                    quit()

        fps.tick(15)


# Main Function
while True:
    
    level = score // 30 + 1
    snake_speed = 15 + (level - 1) * 5 #---------------------------------------------
    
    # handling key events
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                change_to = 'UP'
            if event.key == pygame.K_DOWN:
                change_to = 'DOWN'
            if event.key == pygame.K_LEFT:
                change_to = 'LEFT'
            if event.key == pygame.K_RIGHT:
                change_to = 'RIGHT'

    # If two keys pressed simultaneously
    # we don't want snake to move into two 
    # directions simultaneously
    if change_to == 'UP' and direction != 'DOWN':
        direction = 'UP'
    if change_to == 'DOWN' and direction != 'UP':
        direction = 'DOWN'
    if change_to == 'LEFT' and direction != 'RIGHT':
        direction = 'LEFT'
    if change_to == 'RIGHT' and direction != 'LEFT':
        direction = 'RIGHT'

    # Moving the snake
    if direction == 'UP':
        snake_position[1] -= 10
    if direction == 'DOWN':
        snake_position[1] += 10
    if direction == 'LEFT':
        snake_position[0] -= 10
    if direction == 'RIGHT':
        snake_position[0] += 10

    # Snake body growing mechanism
    # if fruits and snakes collide then scores
    # will be incremented by 10
    snake_body.insert(0, list(snake_position))
    if snake_position[0] == fruit_position[0] and snake_position[1] == fruit_position[1]:
        score += 10
        fruit_spawn = False
    else:
        snake_body.pop()
        
    if not fruit_spawn: #-------------------------------------
        fruit_position = [random.randrange(1, (window_x//10)) * 10, 
                          random.randrange(1, (window_y//10)) * 10]
        
    fruit_spawn = True   #---------------------------------
    game_window.fill(black)
    
    for pos in snake_body:
        pygame.draw.rect(game_window, green,
                         pygame.Rect(pos[0], pos[1], 10, 10))
    pygame.draw.rect(game_window, white, pygame.Rect(
        fruit_position[0], fruit_position[1], 10, 10))

    # Game Over conditions ----------------------------------
    game_over_triggered = False
    if snake_position[0] < 0 or snake_position[0] > window_x-10:
        game_over_triggered = True
    if snake_position[1] < 0 or snake_position[1] > window_y-10:
        game_over_triggered = True

    # Touching the snake body
    for block in snake_body[1:]:
        if snake_position[0] == block[0] and snake_position[1] == block[1]:
            game_over_triggered = True
            break

    if game_over_triggered:
        game_over()
        continue

    # displaying score continuously
    show_score(1, white, 'times new roman', 20)

    # Refresh game screen
    pygame.display.update()

    # Frame Per Second /Refresh Rate
    fps.tick(snake_speed)
