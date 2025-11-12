import pygame
import pickle
from os import path
from pygame import mixer

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 900
screen_height = 900

screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption("Advanced Platformer")

#load images
sun_img = pygame.image.load('img/sun.png')
bg_img = pygame.image.load('img/sky.png')
restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')

#load sounds
pygame.mixer.music.load('img/music.wav')
#pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound("img/coin.wav")
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound("img/jump.wav")
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound("img/game_over.wav")
game_over_fx.set_volume(0.5)
game_won_fx = pygame.mixer.Sound("img/game_won.wav")
game_won_fx.set_volume(0.5)
step_fx = pygame.mixer.Sound("img/step.wav")
step_fx.set_volume(0.5)


# define text font
font_score = pygame.font.SysFont('Bauhaus 93', 30)
font = pygame.font.SysFont('Bauhaus 93', 70)

# define text colors
white = (255, 255, 255)
blue = (0, 0, 255)

#define game variables
tile_size = 45
game_over = 0
main_menu = True
level = 1
max_levels = 7
score = 0

def draw_grid():
    for line in range(20):
        pygame.draw.line(screen,(255,255,255),(0,line * tile_size),(screen_width,line*tile_size),1)
        pygame.draw.line(screen, (255, 255, 255), (line * tile_size,0), (line * tile_size, screen_height), 1)

def draw_text(text, font, text_color, x, y):
    text_img = font.render(text, True, text_color)
    screen.blit(text_img, (x,y))


def reset_level(level):
    global world_data
    player.reset(100,screen_height - 130)
    blob_group.empty()
    lava_group.empty()
    exit_group.empty()
    platform_group.empty()

    #load in level data and create the world
    if path.exists(f'level{level}_data'):
        pickle_in = open(f'level{level}_data', 'rb')
        world_data = pickle.load(pickle_in)

    world = World(world_data)

    return world

class Button():
    def __init__(self,x,y,image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        # get mouse position
        pos = pygame.mouse.get_pos()

        #check mouseover button and clicked condition
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
            if pygame.mouse.get_pressed()[0] == 0 and self.clicked == True:
                self.clicked = False


        #draw button
        screen.blit(self.image,self.rect)
        return action



class Player():
    def __init__(self , x , y):
        self.reset(x,y)

    def update(self, game_over):
        dx = 0
        dy = 0

        if game_over == 0:
            #get key pressed
            key = pygame.key.get_pressed()

            # definim actiunea sariturii
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == True:
                jump_fx.play()
                self.jumped = True
                self.velocity = -15
            if key[pygame.K_SPACE] == False:
                self.jumped = False


            if key[pygame.K_LEFT]:
                self.goes_right = False
                self.counter += 1
                dx -= 5
                self.direction = -1

            if key[pygame.K_RIGHT]:
                self.goes_right = True
                self.counter += 1
                dx += 5
                self.direction = 1

            if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.imges_right[self.index]
                else:
                    self.image = self.imges_left[self.index]


            #handle animation
            if self.counter > 5:
                self.counter = 0
                self.index += 1
                if self.index >= 3:
                    self.index = 0
                if self.direction == 1:
                    self.image = self.imges_right[self.index]
                else:
                    self.image = self.imges_left[self.index]

            #add gravity
            self.velocity += 1
            if self.velocity > 10:
                self.velocity = 10
            dy += self.velocity

            #check for collision with world
            self.in_air = False
            for cell in  world.cell_list:
                # check for horizontal collision
                if cell[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # check for vertical collision
                if cell[1].colliderect(self.rect.x +dx, self.rect.y + dy, self.width, self.height):
                    #check if jumping
                    if self.velocity < 0:
                        dy = cell[1].bottom - self.rect.top
                        self.velocity = 0
                        self.in_air = True
                    #check if falling
                    elif self.velocity >= 0:
                        dy = cell[1].top - self.rect.bottom
                        self.velocity = 0
                        self.in_air = True

            # check collision with enemies
            if pygame.sprite.spritecollide(self, blob_group, False):
                game_over_fx.play()
                game_over = -1

            if pygame.sprite.spritecollide(self, lava_group, False):
                game_over_fx.play()
                game_over = -1

            # check collision with exit
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_won_fx.play()
                game_over = 1

            # check for collision with platforms
            for platform in platform_group:
                # collision in the x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # collision in the y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # check if player is below
                    if abs((self.rect.top + dy) - platform.rect.bottom) < 20:
                        self.velocity = 0
                        dy = platform.rect.bottom - self.rect.top
                    #check is player is above platform
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < 20:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = True
                        dy = 0
                    # move x cross with platform
                    if platform.move_x == 1:
                        self.rect.x += platform.move_direction

            #update player coordonate
            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, screen_width//2 - 200, screen_height//2)
            if self.rect.y > 200:
                self.rect.y -= 5

        screen.blit(self.image, self.rect)
        #pygame.draw.rect(screen, "yellow", self.rect, 2)

        return game_over

    # reset player
    def reset(self, x, y):
        self.imges_right = []
        self.imges_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f"img/guy{num}.png")
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.imges_right.append(img_right)
            self.imges_left.append(img_left)
        self.dead_image = pygame.image.load('img/ghost.png')
        self.image = self.imges_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.velocity = 0
        self.jumped = False
        self.direction = 0
        self.in_air = False

class World():

    def __init__(self,data):
        self.cell_list = []
        #load images
        dirt_img = pygame.image.load('img/dirt.png')
        grass_img = pygame.image.load('img/grass.png')
        coin_img = pygame.image.load('img/coin.png')
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:

                def put_img(upload_image):
                    img = pygame.transform.scale(upload_image, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    cell = (img, img_rect)
                    self.cell_list.append(cell)

                match tile:
                    case 1:
                        put_img(dirt_img)
                    case 2:
                        put_img(grass_img)
                    case 3:
                        blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                        blob_group.add(blob)
                    case 4:
                        platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                        platform_group.add(platform)
                    case 5:
                        platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                        platform_group.add(platform)
                    case 6:
                        lava = Lava(col_count * tile_size, row_count * tile_size + tile_size // 2)
                        lava_group.add(lava)
                    case 7:
                        coin = Coin(col_count * tile_size + tile_size // 4, row_count * tile_size + tile_size // 4)
                        coin_group.add(coin)
                    case 8:
                        exit = Exit(col_count * tile_size, row_count * tile_size - tile_size // 2)
                        exit_group.add(exit)


                col_count+=1
            row_count+=1

    def draw(self):
        for cell in self.cell_list:
            screen.blit(cell[0],cell[1])
            #pygame.draw.rect(screen, "white", cell[1], 2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if self.move_counter > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/lava.png')
        self.image = pygame.transform.scale(img,(tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size//2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if self.move_counter > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Exit(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/exit.png')
        self.image = pygame.transform.scale(img,(tile_size, tile_size * 1.5))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/coin.png')
        self.image = pygame.transform.scale(img,(tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

player = Player(100,screen_height - 130)

blob_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()

score_coin = Coin(tile_size - 40,tile_size - 35)
coin_group.add(score_coin)

#load in level data and create world
if path.exists(f'level{level}_data'):
    pickle_in = open(f'level{level}_data', 'rb')
    world_data = pickle.load(pickle_in)

world = World(world_data)

# create buttons
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img )
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img )

run = True
while run:
    clock.tick(fps)
    screen.blit(bg_img,(0,0))
    screen.blit(sun_img, (100, 100))

    if main_menu == True:
        if exit_button.draw() == True:
            run = False
        if start_button.draw() == True:
            main_menu = False

    else:
        #draw_grid()
        world.draw()

        blob_group.draw(screen)
        lava_group.draw(screen)
        platform_group.draw(screen)
        exit_group.draw(screen)
        coin_group.draw(screen)

        if game_over == 0:
            blob_group.update()
            platform_group.update()
            # update score
            # update if a coin has been collected
            if pygame.sprite.spritecollide(player,coin_group,True):
                score += 1
                coin_fx.play()
            draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)

        game_over = player.update(game_over)

        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0
                score = 0

        if game_over == 1:
            level +=1

            if level <= max_levels:
                #reset level
                world_data = []
                world  = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', font, blue, screen_width//2 - 200, screen_height//2)
                if restart_button.draw():
                    level = 1
                    world_data = []
                    world = reset_level(level)
                    game_over = 0
                    score = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()