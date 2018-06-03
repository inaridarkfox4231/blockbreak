# ブロック崩しできるのかできないのか
# →←キーでパドル移動
# タイミングよく↑キー押すと高速になる(一定時間、落下で解除)
# 高速時はスコアUP, 高速でしか壊せないブロックもある
# スコアは5ステージごとに設定されている。
# 一定以上のスコアを出すとチェックが付いて、
# 全部チェックを付けるとEXTRAが解放される。(21～25, EXTRAとだけ表示)
# MAXで20くらいを想定。（25？）
# 1UPブロックでライフアップ、残りライフもスコアに影響する(1つにつき2000).

import pygame
from pygame.locals import *
import sys
import os
from math import sin, cos, radians, floor
from random import randint

SCR_RECT = Rect(0, 0, 480, 400)
SCR_W = SCR_RECT.width
SCR_H = SCR_RECT.height

MAX_STAGE = 25

TITLE, SELECT, START, PLAY, PAUSE, GAMEOVER, CLEAR, ALLCLEAR = [0, 1, 2, 3, 4, 5, 6, 7]

SCORES = [0, 100, 300, 500, 200, 600, 50, 150]

direction = [23, 45, 67, 113, 135, 157]

def tonum(letter):
    # ABCD...を0123...にする。
    x = ord(letter)
    if x < 97: return x - 65  # 大文字。
    else: return x - 69  # 小文字。

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
        # ここでライフ画像の初期化。
        self.state.life_image_update(self.ball.life)

        clock = pygame.time.Clock()
        self.frame = 0
        self.norm = 0  # 壊すべきブロックの数。
        self.score = 0   # スコア

        while True:
            screen.fill((0, 0, 0))
            clock.tick(60)
            self.update()
            if not self.state.mState in [TITLE, SELECT, START, ALLCLEAR]:
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
        imageList = self.load_image("blockimages1")
        for i in range(5):
            surface = pygame.Surface((40, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 40, 20))
            block.images.append(surface)

        # 壊せる5～9の1×2型。
        imageList = self.load_image("blockimages2")
        for i in range(5):
            surface = pygame.Surface((20, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 20, 40))
            block.images.append(surface)

        # 壊せる10～14の1×1型(通常よりスコア大)。
        imageList = self.load_image("blockimages3")
        for i in range(5):
            surface = pygame.Surface((20, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 20, 20))
            block.images.append(surface)

        # 壊せる15～19の2×2型(通常よりスコア小)。
        imageList = self.load_image("blockimages4")
        for i in range(5):
            surface = pygame.Surface((40, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 40, 40))
            block.images.append(surface)

        # ノルムが関係するのは0～19のブロック「だけ」なので注意する。

        # 壊せる20～22の1×2型。すべて壊さなくてもクリア可能。
        # 14は1回で壊れる、壊すと1UP. 15と16は高速でないと壊れないタイプ
        # 15は緑で高速1回、16は黄緑で2回。いずれも500点追加。
        # 23～25で縦型も用意したい。
        imageList = self.load_image("blockimages5")
        for i in range(3):
            surface = pygame.Surface((40, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 40, 20))
            block.images.append(surface)

        imageList = self.load_image("blockimages6")
        for i in range(3):
            surface = pygame.Surface((20, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 20, 40))
            block.images.append(surface)

        # 上部、両サイド(26と27, 26以降はすべて壊せないブロック。).
        surface = self.load_image("blockupper")
        block.images.append(surface)
        surface = self.load_image("blockside")
        block.images.append(surface)

        # ここに20種類の壊せないブロック(28～47)を記述。
        # 小文字のaが97だから69を引いてコード番号にする。
        # 本当はエディタで作って16進数2桁で保存する方がいいって分かってるけどね。
        imageList = self.load_image("blockimages7")
        for i in range(10):
            surface = pygame.Surface((20 * (i + 1), 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 20 * (i + 1), 20))
            block.images.append(surface)

        imageList = self.load_image("blockimages8")
        for i in range(10):
            surface = pygame.Surface((20, 20 * (i + 1)))
            surface.blit(imageList, (0, 0), (20 * i, 0, 20, 20 * (i + 1)))
            block.images.append(surface)

        imageList = self.load_image("paddleimages")
        for i in range(2):
            surface = pygame.Surface((80, 5))
            surface.blit(imageList, (0, 0), (0, 5 * i, 80, 5))
            paddle.images.append(surface)

        imageList = self.load_image("ballimages")
        for i in range(2):
            surface = pygame.Surface((16, 16))
            surface.blit(imageList, (0, 0), (16 * i, 0, 16, 16))
            surface.set_colorkey(surface.get_at((0, 0)), RLEACCEL)
            ball.images.append(surface)

        # 発射方向のポインター。
        self.dirimage = self.load_image("pointerimage")

        # 各種テキスト
        imageList = self.load_image("TEXTS")
        widths = [160, 340, 80, 80, 200, 120, 280, 165, 95, 145, 180, 370, 85]
        for i in range(13):
            surface = pygame.Surface((widths[i], 30))
            surface.blit(imageList, (0, 0), (0, 30 * i, widths[i], 30))
            GameState.texts.append(surface)

        # 各種数字画像(*追加)
        imageList = self.load_image("NUMBERS")
        for i in range(11):
            surface = pygame.Surface((18, 30))
            surface.blit(imageList, (0, 0), (18 * i, 0, 18, 30))
            GameState.numbers.append(surface)

        # 各種選択肢画像
        imageList = self.load_image("CHOICES")
        for i in range(14):
            w = 180
            if w % 7 == 0: w = 65
            elif w % 7 == 1: w = 130
            surface = pygame.Surface((w, 30))
            surface.blit(imageList, (0, 0), (0, 30 * i, w, 30))
            GameState.choices.append(surface)

    def pre_loading(self):
        self.blocks.empty()  # 一旦空にする
        self.norm = 0        # ノルムリセット。

        data = []
        fp = open(self.load_stage(self.state.stage), "r")
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

            prev = [0, 0]
            prev[0] = self.score
            prev[1] = self.ball.life
            
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

            self.score += SCORES[dmg] # グローバルで書いた。

            if prev[0] != self.score:
                self.state.score_image_update(prev[0], self.score)
            if prev[1] != self.ball.life:
                self.state.life_image_update(self.ball.life)

    def draw(self, screen):

        self.blocks.draw(screen)
        self.paddle.draw(screen)
        self.ball.draw(screen)

        self.state.draw_status(screen)  # stateの方で描画

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
                self.state.write_data()  # データの書き込み(セーブ)
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                self.keydown_event(event.key)

    def keydown_event(self, key):
        if key == K_ESCAPE:
            self.state.write_data()   # データの書き込み(セーブ)
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
            if to_reset:
                self.reset()

        # ALLCLEARのときに1回だけボーナス追加。
        if self.state.mState == ALLCLEAR and self.ball.life > 0:
            bonus = self.add_bonus()
            # ここでGameStateにスコアデータを更新してもらう。
            self.state.hi_score_update(bonus, self.score)

    def reset(self):
        self.state.mState = TITLE

        self.state.life_image_update(ball.maxlife)    # ライフのイメージを設定。
        self.ball.life = ball.maxlife
        self.state.score_image_update(self.score, 0)  # 先にイメージを変更しないと。
        self.score = 0

        self.state.stage = 1  # ステージを戻す

    def add_bonus(self):
        # ALLCLEAR時にボーナス追加。
        bonus = self.ball.life * 2000
        self.state.score_image_update(self.score, self.score + bonus)
        self.score += bonus
        self.ball.life = 0
        return bonus  # bonusが戻る。

    def load_image(self, filename, flag = False):
        """画像のロード"""
        filename += ".png"
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
    texts = []   # テキスト関係
    numbers = []  # 数字関係（0123456789)(*追加)
    choices = []  # 選択肢関係
    def __init__(self):
        self.mState = TITLE
        self.font = pygame.font.SysFont(None, 40)
        self.cursol = 0
        self.stage = 1

        self.life_image = []     # ステータスバーに表示する残りライフの画像。
        for i in range(2):
            self.life_image.append(self.numbers[0])
        self.score_image = []    # ステータスバーに表示するスコアの画像。
        for i in range(6):
            self.score_image.append(self.numbers[0])

        self.backup = []  # 解放状況、ハイスコア、フラグ。
        self.read_data()  # textデータ読み込み
        self.limit = 0    # 解放状況、たとえば2なら1～10まで。
        for i in range(5):
            if self.backup[i] > 0: self.limit += 1
            else: break

        self.score_board = []    # 1～5のハイスコアとボーナスの、うん。
        for i in range(5):
            n = self.backup[i + 5]  # 5, 6, 7, 8, 9のところ。
            line = []
            for i in range(6):
                line.append(self.numbers[n % 10]) # ハイスコア表示用のスペース。
                n //= 10
            self.score_board.append(line)
        line = []
        for i in range(5): line.append(self.numbers[0])
        self.score_board.append(line)  # ボーナス表示用のスペース。

    def life_image_update(self, new_life):
        # ライフ画像の更新
        self.life_image[0] = self.numbers[new_life % 10]
        self.life_image[1] = self.numbers[new_life // 10]

    def score_image_update(self, old_sc, new_sc):
        # スコア画像の更新
        i = 0
        while old_sc != new_sc:
            if old_sc % 10 != new_sc % 10:
                self.score_image[i] = self.numbers[new_sc % 10]
            old_sc //= 10
            new_sc //= 10
            i += 1    

    def draw_status(self, screen):
        screen.blit(self.texts[12], (5, 5))    # LIFE
        screen.blit(self.texts[8], (144, 5))   # SCORE
        for i in range(2):
            screen.blit(self.life_image[1 - i], (90 + 18 * i, 5))
        for i in range(6):
            screen.blit(self.score_image[5 - i], (240 + 18 * i, 5))

    def draw(self, screen):
        if self.mState == TITLE:
            screen.blit(self.texts[0], (200, 120))  # TITLE
            screen.blit(self.texts[1], (140, 180))  # PRESS ENTER KEY

        elif self.mState == SELECT:
            # 選択しているところは黒文字
            index = [i + 1 for i in range(6)]
            index[self.cursol] += 7  # 黒文字

            screen.blit(self.choices[index[0]], (80, 100))
            screen.blit(self.texts[9], (280, 100))  # Hi-SCORE

            for i in range(self.limit):
                screen.blit(self.choices[index[i + 1]], (80, 160 + 40 * i))
                for k in range(6):  # ハイスコア表示できるようにしてみた。
                    screen.blit(self.score_board[i][5 - k], (280 + 18 * k, 160 + 40 * i))
                if self.backup[i] == 3:
                    screen.blit(self.numbers[10], (60, 160 + 40 * i))
            # あとは、0なら表示しない、それと、3なら*をつける、かな・・

        elif self.mState == START:
            screen.blit(self.texts[2], (160, 120))  # STAGE
            screen.blit(self.numbers[self.stage // 10], (258, 120))
            screen.blit(self.numbers[self.stage % 10], (276, 120))

        elif self.mState == PAUSE:
            screen.blit(self.texts[3], (200, 120))  # PAUSE

            index = [0, 1]
            index[self.cursol] += 7  # 黒文字
            screen.blit(self.choices[index[0]], (240, 200))
            screen.blit(self.choices[index[1]], (240, 240))

        elif self.mState == GAMEOVER:
            screen.blit(self.texts[4], (200, 120))  # GAME OVER...
            screen.blit(self.texts[1], (120, 180))  # PRESS ENTER KEY

        elif self.mState == CLEAR:
            screen.blit(self.texts[5], (200, 120))  # CLEAR!!

            if self.stage % 5 == 0:
                screen.blit(self.texts[6], (120, 180))  # STAGE ALL CLEAR!!
            screen.blit(self.texts[1], (120, 240))  # PRESS ENTER KEY

        elif self.mState == ALLCLEAR:
            screen.blit(self.texts[7], (100, 100))  # LIFE BONUS
            screen.blit(self.texts[8], (100, 160))  # SCORE
            screen.blit(self.texts[9], (100, 220))  # Hi-SCORE
            if self.backup[10] == 1:
                screen.blit(self.texts[11], (100, 260))  # Hi-SCORE UPDATE!!
            screen.blit(self.texts[1], (100, 320))  # PRESS ENTER KEY
            for i in range(5):
                screen.blit(self.score_board[5][4 - i], (270 + 18 * i, 100))
            for i in range(6):
                screen.blit(self.score_image[5 - i], (200 + 18 * i, 160))
            x = self.stage // 5 - 1
            for i in range(6):
                screen.blit(self.score_board[x][5 - i], (250 + 18 * i, 220))

    def keydown_events(self, key):
        if self.mState == TITLE:
            if key == K_RETURN:
                self.mState = SELECT
            return False

        if self.mState == SELECT:
            if key == K_DOWN:
                self.cursol = (self.cursol + 1) % (self.limit + 1)

            elif key == K_UP:
                if self.cursol > 0:
                    self.cursol = (self.cursol + self.limit) % (self.limit + 1)
                else:
                    self.cursol = self.limit
                
            elif key == K_RETURN:
                if self.cursol == 0:
                    self.mState = TITLE
                else:
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
                    self.mState = ALLCLEAR
                    # 次のステージに行けるようにする。
                    return False  # stageはこっちで1に戻す感じ。
                else:
                    self.mState = START; return False
        # ALLCLEARからENTERキー押してTITLEに戻るのでここはFalseで。

        if self.mState == ALLCLEAR:
            if key == K_RETURN:
                self.mState = TITLE
                # ここでステージの解放、及び、
                # 3 3 3 3でかつ0なら1にする処理を挟む。
                # ついでに書き込みも忘れずに。
                x = self.stage // 5
                if x < 4 and self.backup[x] == 0:
                    self.backup[x] = 1 # 次のステージ組解放
                    self.limit += 1
                if self.backup[4] == 0 and self.backup[0] + self.backup[1] + self.backup[2] + self.backup[3] == 12:
                    self.backup[4] = 1  # EXTRA解放
                    self.limit = 5      # limitをMAXに。
                self.backup[10] = 0  # フラグを消す。
                return True

    def read_data(self):
        # データの読み込み
        filename = os.path.join("stages", "scores.txt")
        fp = open(filename, "r")
        data = []
        for row in fp:
            row = row.rstrip()
            data = row.split()  # 改行取ってスペース区切り。
        fp.close()
        # 始めの5つは0, 1, 3で、その後の5つがスコアー。最後のは
        # ハイスコアを更新するとき1になるフラグ。
        for i in range(10): self.backup.append(int(data[i]))
        self.backup.append(0)

    def write_data(self):
        # データの書き込み
        filename = os.path.join("stages", "scores.txt")
        fp = open(filename, "w")
        fp.write(str(self.backup[0]))
        for i in range(1, 10):
            fp.write(" " + str(self.backup[i]))
        fp.close()

    def hi_score_update(self, bonus, score):
        # ここで全部やる。(0)bonus画像設定、さらにscore(最終スコア)と
        # stageから分かるそのステージ組のハイスコアを比べて上がるようなら
        # (1)ハイスコアbackupの更新、(2)表示画像の更新、
        # (3)1→3になるようならそこを更新。このデータを元にALLCLEAR画面にあれする。
        for i in range(5):
            self.score_board[5][i] = self.numbers[bonus % 10]
            bonus //= 10
        x = self.stage // 5 - 1
        if score > self.backup[5 + x]:
            if self.backup[x] == 1: self.backup[x] = 3
            self.backup[5 + x] = score
            for i in range(6):
                self.score_board[x][i] = self.numbers[score % 10]
                score //= 10
            self.backup[10] = 1  # フラグ。テキスト表示用。

if __name__ =="__main__":
    Play()
