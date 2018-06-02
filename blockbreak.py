# ブロック崩しできるのかできないのか
# →←キーでパドル移動
# タイミングよく↑キー押すと高速になる(一定時間、落下で解除)
# 高速時はスコアUP, 高速でしか壊せないブロックもある
# スコアは5ステージごとに設定されている。
# 一定以上のスコアを出すとチェックが付いて、
# 全部チェックを付けるとEXTRAが解放される。(21～25, EXTRAとだけ表示)
# MAXで20位を想定。
# 1UPブロックでライフアップ、残りライフもスコアに影響する。
# 今後：エディタでステージ作れるようにしたい
# 壊せないブロックをもっと活用したい

import pygame
from pygame.locals import *
import sys
import os
from math import sin, cos, atan, radians, floor, pi
from random import randint

SCR_RECT = Rect(0, 0, 480, 400)
SCR_W = SCR_RECT.width
SCR_H = SCR_RECT.height

MAX_STAGE = 20

TITLE, SELECT, START, PLAY, PAUSE, GAMEOVER, CLEAR, RANK = [0, 1, 2, 3, 4, 5, 6, 7]

SCORES = [0, 100, 300, 500, 200, 600, 50, 150]

direction = [23, 45, 67, 113, 135, 157]

def tonum(letter):
    # ABCD...を0123...にする。
    x = ord(letter)
    if x < 97: return x - 65  # 大文字。
    else: return x - 69
    # return ord(letter) - 65
    # ここをいじって小文字使えるようにしたい

def calc_ballpos(rect, pos):
    x = pos[0]; y = pos[1]
    if y > rect.bottom:
        if x > rect.right: return 1
        elif x < rect.left: return 3
        else: return 2
    elif y < rect.top:
        if x > rect.right: return 7
        elif x < rect.left: return 5
        else: return 6
    else:
        if x > rect.right: return 0
        elif x < rect.left: return 4
        else: return -1

def calc_is_far(rect, pos):
    # 離れてるのは計算しない
    dx = abs(rect.centerx - pos[0]) - rect.width // 2
    dy = abs(rect.centery - pos[1]) - rect.height // 2
    return max(dx, dy) > 40

def calc_reflect(cornerpos, ballpos, speed):
    # 新しい速度を返す関数
    a, b = cornerpos
    theta = radians(randint(30, 60))  # 角に当たったらランダムで反射。
    newvx = 0.1 * floor(cos(theta) * 10 * speed)
    newvy = 0.1 * floor(sin(theta) * 10 * speed)
    return (newvx, newvy)

class Play():
    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode(SCR_RECT.size)
        pygame.display.set_caption("blockbreak_1")

        self.blocks = pygame.sprite.RenderUpdates()
        block.containers = self.blocks

        self.loading();
        self.paddle = paddle((200, 380))
        self.ball = ball((232, 368), self.blocks, self.paddle)

        self.state = GameState()  # Stateの初期化
        self.font = pygame.font.SysFont(None, 40)

        clock = pygame.time.Clock()
        self.frame = 0
        self.norm = 0  # 壊すべきブロックの数。
        self.score = 0   # スコア
        self.ranking = []  # ランキングデータ、0, 1, 2, 3ごとに5ステージずつ。

        while True:
            screen.fill((0, 0, 0))
            clock.tick(60)
            self.update()
            if not self.state.mState in [TITLE, SELECT, START]:
                self.draw(screen)
            self.state.draw(screen)
            pygame.display.update()

            if self.state.mState == PLAY:
                if self.ball.life == 0:
                    self.state.mState = GAMEOVER
                elif self.norm == 0:
                    self.state.mState = CLEAR

            self.key_handler()
            
    def loading(self):
        # 壊せる0～4の2×1型。
        imageList = pygame.image.load("blockimages1.png")
        for i in range(5):
            surface = pygame.Surface((40, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 40, 20))
            block.images.append(surface)

        # 壊せる5～9の1×2型。
        imageList = pygame.image.load("blockimages2.png")
        for i in range(5):
            surface = pygame.Surface((20, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 20, 40))
            block.images.append(surface)

        # 壊せる10～14の1×1型(通常よりスコア大)。
        imageList = pygame.image.load("blockimages3.png")
        for i in range(5):
            surface = pygame.Surface((20, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 20, 20))
            block.images.append(surface)

        # 壊せる15～19の2×2型(通常よりスコア小)。
        imageList = pygame.image.load("blockimages4.png")
        for i in range(5):
            surface = pygame.Surface((40, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 40, 40))
            block.images.append(surface)

        # ノルムが関係するのは0～19のブロック「だけ」なので注意する。

        # 壊せる20～22の1×2型。すべて壊さなくてもクリア可能。
        # 14は1回で壊れる、壊すと1UP. 15と16は高速でないと壊れないタイプ
        # 15は緑で高速1回、16は黄緑で2回。いずれも500点追加。
        # 23～25で縦型も用意したい。
        imageList = pygame.image.load("blockimages5.png")
        for i in range(3):
            surface = pygame.Surface((40, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 40, 20))
            block.images.append(surface)

        imageList = pygame.image.load("blockimages6.png")
        for i in range(3):
            surface = pygame.Surface((20, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 20, 40))
            block.images.append(surface)

        # 上部、両サイド(26と27, 26以降はすべて壊せないブロック。).
        surface = pygame.image.load("blockupper.png")
        block.images.append(surface)
        surface = pygame.image.load("blockside.png")
        block.images.append(surface)

        # ここに20種類の壊せないブロック(28～47)を記述。
        # 小文字のaが97だから69を引いてコード番号にする。
        # 本当はエディタで作って16進数2桁で保存する方がいいって分かってるけどね。
        imageList = pygame.image.load("blockimages7.png")
        for i in range(10):
            surface = pygame.Surface((20 * (i + 1), 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 20 * (i + 1), 20))
            block.images.append(surface)

        imageList = pygame.image.load("blockimages8.png")
        for i in range(10):
            surface = pygame.Surface((20, 20 * (i + 1)))
            surface.blit(imageList, (0, 0), (20 * i, 0, 20, 20 * (i + 1)))
            block.images.append(surface)

        imageList = pygame.image.load("paddleimages.png")
        for i in range(2):
            surface = pygame.Surface((80, 5))
            surface.blit(imageList, (0, 0), (0, 5 * i, 80, 5))
            paddle.images.append(surface)

        imageList = pygame.image.load("ballimages.png")
        for i in range(2):
            surface = pygame.Surface((16, 16))
            surface.blit(imageList, (0, 0), (16 * i, 0, 16, 16))
            surface.set_colorkey(surface.get_at((0, 0)), RLEACCEL)
            ball.images.append(surface)

        # 発射方向のポインター。
        self.dirimage = pygame.image.load("pointerimage.png")

    def pre_loading(self):
        self.blocks.empty()  # 一旦空にする
        self.norm = 0        # ノルムリセット。

        data = []
        fp = open("bbstage" + str(self.state.stage) + ".map", "r")
        for line in fp:
            line = line.rstrip()
            data.append(list(line))
        fp.close()
        row = len(data)
        col = len(data[0])
        for j in range(row):
            for i in range(col):
                if data[j][i] == '.': continue
                n = tonum(data[j][i])
                block((20 + 20 * i, 60 + 20 * j), n)
                if n < 20: self.norm += 1  # 0～19のブロックだけ加算する。

        # 壁は共通。
        block((20, 40), 26)  # 天井の壁
        block((0, 40), 27); block((460, 40), 27)  # 両サイドの壁

        # パドルとボールのリセット
        self.paddle.rect.topleft = (200, 395)
        # ボールの位置は初期設定不要（resetでset_onになったらupdateがやってくれる）
        self.ball.reset()

    def update(self):
        if self.state.mState == START:
            if self.frame == 0:
                self.pre_loading()
                self.frame = 60
            else:
                self.frame -= 1
                if self.frame == 0:
                    self.state.mState = PLAY

        if self.state.mState == PLAY:
            for block in self.blocks:
                if block.update():
                    if block.kind < 20:
                        self.norm -= 1  # ノルマに加算するのは0～19だけ
                block.far = calc_is_far(block.rect, self.ball.rect.center)
                if not block.far:
                    block.ballpos = calc_ballpos(block.rect, self.ball.rect.center)
            self.paddle.ballpos = calc_ballpos(self.paddle.rect, self.ball.rect.center)
            self.paddle.far = calc_is_far(self.paddle.rect, self.ball.rect.center)
            self.paddle.update()
            dmg = self.ball.update()
            if dmg == 0: return
            else:
                self.score += SCORES[dmg] # グローバルで書いた。

    def draw(self, screen):

        self.blocks.draw(screen)
        self.paddle.draw(screen)
        self.ball.draw(screen)

        # ↓statusってのを別に用意してそっちで描画する
        text = self.font.render("life: " + str(self.ball.life), False, (255, 255, 255))
        screen.blit(text, (0, 0))
        text = self.font.render("score: " + str(self.score), False, (255, 255, 255))
        screen.blit(text, (120, 0))

        if self.state.mState == GAMEOVER: return

        if self.ball.set_on:
            self.frame += 1
            if self.frame > 191: self.frame = 0
            x, y = self.ball.rect.center
            dx = floor(cos(radians(direction[self.frame // 32])) * 20)
            dy = -floor(sin(radians(direction[self.frame // 32])) * 20)
            screen.blit(self.dirimage, (x + dx, y + dy))

    def key_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                self.keydown_event(event.key)

    def keydown_event(self, key):
        if key == K_ESCAPE:
            pygame.quit()
            sys.exit()
        if self.state.mState == PLAY:
            if key == K_SPACE and self.ball.set_on:
                dx = cos(radians(direction[self.frame // 32]))
                dy = sin(radians(direction[self.frame // 32]))
                self.ball.fpvx = 0.1 * floor(dx * self.ball.speed * 10)
                self.ball.fpvy = 0.1 * floor(dy * self.ball.speed * 10)
                self.frame = 0
                self.ball.set_on = False  # ボールがパドルから離れる
            elif key == K_UP and not self.ball.set_on and self.paddle.count == 0:
                self.paddle.count = 16
                self.paddle.image = paddle.images[1]
            elif key == K_LCTRL and not self.ball.set_on:  # ボールがパドル上にあるときはポーズ不可。
                self.state.mState = PAUSE  # 左CTRLキーでポーズ

        else:
            to_reset = self.state.keydown_events(key)  # ここでなんか返す
            if to_reset: self.reset()

    def reset(self):
        self.state.mState = TITLE
        self.ball.life = ball.maxlife
        self.score = 0
        self.state.stage = 1  # ステージを戻す

    def load_image(self, filename, flag = False):
        """画像のロード"""
        filename = os.path.join("images", filename)
        image = pygame.image.load(filename).convert()
        if not flag: return image
        else:
            colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, RLEACCEL)
        return image

    def load_stage(self, stage):
        """ステージのロード"""
        filename = "bbstage" + str(stage) + ".map"
        filename = os.path.join("stages", filename)
        return filename

class block(pygame.sprite.Sprite):
    images = []
    def __init__(self, pos, kind):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.kind = kind
        self.image = self.images[self.kind]
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.tough = self.set_tough()  # いずれkindにより種別する
        self.ballpos = -1  # 衝突判定用
        self.far = True    # ボールが遠くにあるときに判定しない
        
    def set_tough(self):
        if self.kind < 20: return (self.kind % 5) + 1  # 通常ブロック
        if self.kind == 20 or self.kind == 21 or self.kind == 23 or self.kind == 24: return 1
        if self.kind == 22 or self.kind == 25: return 2
        # 26以降は壊せないブロック。
        return -1

    def break_off(self, dmg):
        if self.tough < 0: return 0  # 壊せないブロック(ダメージ0を返す)
        if self.kind < 20:
            # 通常のブロック(青→紫→赤→橙→黄)
            self.tough = max(self.tough - dmg, 0)
            if self.tough > 0:
                self.kind -= dmg
                self.image = self.images[self.kind]
            if self.kind < 10: return dmg
            elif self.kind < 15: return 3 + dmg # 4が200, 5が600.
            else: return 5 + dmg # 6が50, 7が150のパス。大きいので低スコア。
        else:
            # ピンクのブロック
            if self.kind == 20 or self.kind == 23: self.tough = 0; return 1
            # 緑のブロック
            if self.kind == 21 or self.kind == 24:
                if dmg > 1: self.tough = 0; return 3
                else: return 0
            # 黄緑のブロック(→緑)
            if self.kind == 22 or self.kind == 25:
                if dmg > 1:
                    self.tough -= 1; self.kind -= 1
                    self.image = self.images[self.kind]; return 3
                else:
                    return 0
        return 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.tough == 0:
            self.kill()
            return 1
        return 0  # ブロックが壊れたら1を返す。

class paddle:
    images = []
    def __init__(self, pos):
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.vx = 0
        self.ballpos = -1 # 衝突判定用
        self.far = False  # ボールが遠くにあるときに判定しない
        self.count = 0    # 0～32の範囲で動く、32～16のときに赤く光る

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[K_RIGHT]:
            self.vx = 6
        elif keys[K_LEFT]:
            self.vx = -6
        else:
            self.vx = 0
        if self.rect.left + self.vx < 20: self.vx = 0
        if self.rect.right + self.vx > SCR_W - 20: self.vx = 0
        self.rect.x += self.vx
        # カウントは16～0で、16～8のときに光ってる感じ。
        if self.count > 0:
            self.count -= 1
            if self.count < 8: self.image = self.images[0]

class ball:
    r = 8
    speed = 4.0  # スピードアップ時は6.0にする。クラス変数は変更可能。
    maxlife = 10
    images = []
    def __init__(self, pos, blocks, paddle):
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos[0], pos[1])
        self.blocks = blocks  # 衝突判定用
        self.paddle = paddle
        self.fpvx = 0.0
        self.fpvy = 0.0
        self.fpx = float(pos[0])
        self.fpy = float(pos[1])
        self.set_on = True
        self.count = 0   # 強化してる時用のカウント
        self.life = self.maxlife   # 10回落ちたら終了

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.set_on:
            self.rect.x = self.paddle.rect.x + self.paddle.rect.width // 2 - self.r
            self.rect.y = self.paddle.rect.y - self.rect.height
            self.fpx = float(self.rect.x)
            self.fpy = float(self.rect.y)
            return 0  # ここ。Noneになってしまうよ。
        
        # ブロックと衝突判定
        # 1. farなのはスルー。2. 移動後の座標で衝突しないものはスルー。
        # 3. 衝突するならフラグに従って、偶数フラグなら値により速度反転、
        # 奇数フラグ(角っちょ)の場合は当たり方によって方向をいじる感じ。
        dmg = self.collideblock()  # ダメージを記録               
        
        # パドルと衝突判定
        self.collidepaddle()

        # 位置更新
        self.fpx += self.fpvx
        self.fpy += self.fpvy
        self.rect.x = int(self.fpx)
        self.rect.y = int(self.fpy)
        
        # 落下判定
        if self.rect.top > SCR_H:
            self.life -= 1  # ライフを減らす
            self.reset()

        if self.count > 0:
            self.count -= 1
            if self.count == 0:
                self.speed = 4.0
                self.fpvx = floor(self.fpvx * 6.6) * 0.1
                self.fpvy = floor(self.fpvy * 6.6) * 0.1
                self.image = self.images[0]

        return dmg  # ダメージを返す

    def collideblock(self):
        newrect = Rect(int(self.rect.x + self.fpvx), int(self.rect.y + self.fpvy), 16, 16)
        for block in self.blocks:
            if block.far: continue
            if newrect.colliderect(block.rect):
                phase = block.ballpos
                if phase == 0 or phase == 4: self.fpvx = -self.fpvx
                if phase == 2 or phase == 6: self.fpvy = -self.fpvy
                if phase & 1 == 0:
                    # ここにブロック壊した際のたとえば1UPとか記述(20と23)
                    if block.kind == 20 or block.kind == 23: self.life += 1
                    if self.count == 0: return block.break_off(1)
                    else: return block.break_off(2)

                newv = (0, 0)
                if phase == 1:
                    newv = calc_reflect(block.rect.bottomright, newrect.center, self.speed)
                    self.fpvx = newv[0]; self.fpvy = newv[1]
                elif phase == 3:
                    newv = calc_reflect(block.rect.bottomleft, newrect.center, self.speed)
                    self.fpvx = -newv[0]; self.fpvy = newv[1]
                elif phase == 5:
                    newv = calc_reflect(block.rect.topleft, newrect.center, self.speed)
                    self.fpvx = -newv[0]; self.fpvy = -newv[1]
                elif phase == 7:
                    newv = calc_reflect(block.rect.topright, newrect.center, self.speed)
                    self.fpvx = newv[0]; self.fpvy = -newv[1]
                # ここにたとえば1UPとか記述(20と23)
                if block.kind == 20 or block.kind == 23: self.life += 1
                if self.count == 0: return block.break_off(1)
                else: return block.break_off(2)
                break  # ひとつで充分
        return 0

    def collidepaddle(self):
        if self.paddle.far: return
        newrect = Rect(int(self.rect.x + self.fpvx), int(self.rect.y + self.fpvy), 16, 16)
        if not newrect.colliderect(self.paddle.rect): return
        phase = self.paddle.ballpos
        if phase == 6:
            self.fpvy = -self.fpvy
            if self.paddle.count & 8 and self.count == 0:  # 強化(複数回強化しないよう修正)
                self.count = 300; self.speed = 6.0;
                self.fpvx = floor(self.fpvx * 15) * 0.1
                self.fpvy = floor(self.fpvy * 15) * 0.1
                self.image = self.images[1]
            return
        if phase == 0 or phase == 4: self.fpvx = -self.fpvx; return
        if phase == 5:
            newv = calc_reflect(self.paddle.rect.topleft, newrect.center, self.speed)
            self.fpvx = -newv[0]; self.fpvy = -newv[1]
        elif phase == 7:
            newv = calc_reflect(self.paddle.rect.topright, newrect.center, self.speed)
            self.fpvx = newv[0]; self.fpvy = -newv[1]

    def reset(self):
        if self.life == 0: return  # lifeが0のときは何もしない
        self.set_on = True
        self.speed = 4.0
        self.image = self.images[0]
        self.count = 0

class GameState:
    images = []  # テキスト関係
    def __init__(self):
        self.mState = TITLE
        self.font = pygame.font.SysFont(None, 40)
        self.cursol = 0
        self.stage = 1
        self.stage_playable = 4  # 5つクリアするたびに1ずつ増えていく感じ。
        
    def drawtext(self, screen, words, location, flag = False):
        if not flag:
            text = self.font.render(words, False, (255, 255, 255), (0, 0, 0))
        else:
            text = self.font.render(words, False, (0, 0, 0), (255, 255, 255))
        screen.blit(text, location)

    def draw(self, screen):
        if self.mState == TITLE:
            self.drawtext(screen, "BLOCKBREAK", (200, 120))
            flag = []
            if self.cursol == 0: flag = [True, False]
            else: flag = [False, True]
            self.drawtext(screen, "PLAY", (240, 200), flag[0])
            self.drawtext(screen, "RANK", (240, 240), flag[1])

        elif self.mState == SELECT:
            # 選択しているところは黒文字
            flag = []
            for i in range((MAX_STAGE // 5) + 1): flag.append(False)
            flag[self.cursol] = True
            
            self.drawtext(screen, "TO  TITLE", (200, 100), flag[0])
            for i in range(MAX_STAGE // 5):
                words = "STAGE " + str((i * 5) + 1) + " - " + str((i + 1) * 5)
                # 挑戦可能なステージには"*"を付加する
                if i + 1 <= self.stage_playable: words += " *"
                self.drawtext(screen, words, (200, 160 + 40 * i), flag[i + 1])

        elif self.mState == START:
            self.drawtext(screen, "STAGE " + str(self.stage), (200, 120))

        elif self.mState == PAUSE:
            self.drawtext(screen, "PAUSE", (200, 120))
            flag = []
            if self.cursol == 0: flag = [True, False]
            else: flag = [False, True]
            self.drawtext(screen, "PLAY", (240, 200), flag[0])
            self.drawtext(screen, "TO  TITLE", (240, 240), flag[1])

        elif self.mState == GAMEOVER:
            self.drawtext(screen, "GAME  OVER", (200, 120))
            self.drawtext(screen, "PRESS  RETURN", (200, 180))

        elif self.mState == CLEAR:
            self.drawtext(screen, "CLEAR!!", (200, 120))
            if self.stage % 5 == 0:
                self.drawtext(screen, "STAGE ALL CLEAR!!", (120, 180))
            self.drawtext(screen, "PRESS  RETURN", (200, 240))

    def keydown_events(self, key):
        if self.mState == TITLE:
            if key == K_DOWN or key == K_UP:
                self.cursol = (self.cursol + 1) % 2
            elif key == K_RETURN:
                if self.cursol == 0:
                    self.mState = SELECT
                # 2(RANK)は工事中
            return False

        if self.mState == SELECT:
            if key == K_DOWN:
                self.cursol = (self.cursol + 1) % ((MAX_STAGE // 5) + 1)

            elif key == K_UP:
                if self.cursol > 0:
                    self.cursol = (self.cursol - 1) % ((MAX_STAGE // 5) + 1)
                else:
                    self.cursol = MAX_STAGE // 5
                
            elif key == K_RETURN:
                if self.cursol == 0:
                    self.mState = TITLE
                else:
                    if self.cursol > self.stage_playable: return False
                    self.mState = START
                    self.stage = (self.cursol * 5) - 4
                    self.cursol = 0
                return False

        if self.mState == PAUSE:
            if key == K_DOWN or key == K_UP:
                self.cursol = (self.cursol + 1) % 2; return False
            elif key == K_RETURN:
                if self.cursol == 0:
                    self.mState = PLAY; return False
                elif self.cursol == 1:
                    self.mState = TITLE
                    self.cursol = 0; return True

        elif self.mState == GAMEOVER:
            if key == K_RETURN:
                self.mState = TITLE; return True

        if self.mState == CLEAR:
            if key == K_RETURN:
                self.stage += 1
                if self.stage % 5 == 1:  # 6, 11, ...の時にリセット。
                    self.mState = TITLE
                    # 次のステージに行けるようにする。
                    self.stage_playable = max(self.stage_playable, (self.stage // 5) + 1)
                    self.stage_playable = min(self.stage_playable, MAX_STAGE // 5)
                    return True  # stageはこっちで1に戻す感じ。
                else:
                    self.mState = START; return False

if __name__ =="__main__":
    Play()