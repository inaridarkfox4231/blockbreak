# ブロック崩しできるのかできないのか
# マウス操作でパドル移動
# タイミングよく左クリックすると高速になる(一定時間、落下で解除)
# 高速時はスコアUP, 高速でしか壊せないブロックもある
# EASY, NORMAL, HARDがあって、HARDクリアするとチェックが付く。
# 全部チェックを付けるとEXTRAが解放される。(21～25, EXTRAとだけ表示)
# EXTRAもHARDでクリアするとお楽しみとしてCLAZYが解禁。以上。
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

TITLE, SELECT, MODE = [0, 1, 2]
START, PLAY, PAUSE, GAMEOVER, CLEAR, ALLCLEAR = [3, 4, 5, 6, 7, 8]

SCORES = [0, 100, 250, 500, 150, 400, 50, 100]

direction = [23, 45, 67, 113, 135, 157]

MAX_LIFE = [3, 5, 10, 13]
PADDLE_TYPE = [0, 1, 2, 3]

def tonum(letter):
    # ABCD...を0123...にする。
    x = ord(letter)
    if x < 97: return x - 65  # 大文字。
    else: return x - 97 + 26  # 小文字。

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
        pygame.display.set_caption("blockbreak")

        self.blocks = pygame.sprite.RenderUpdates()
        block.containers = self.blocks

        self.loading()

        self.state = GameState()  # Stateの初期化

        clock = pygame.time.Clock()
        
        self.frame = 0  # リセット時のポインタの場所を・・消すかも（パドルに委ねる）

        self.norm = 0  # 壊すべきブロックの数。
        self.score = 0   # スコア

        while True:
            screen.fill((0, 0, 0))
            clock.tick(60)
            self.update()
            if not self.state.mState in [TITLE, SELECT, MODE, START, ALLCLEAR]:
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

        # ブロックのrect.
        rectseries = []
        for i in range(8): rectseries.append([])
        for i in range(5): rectseries[0].append(Rect(0, 20 * i, 40, 20))
        for i in range(5): rectseries[1].append(Rect(0, 40 * i, 20, 40))
        for i in range(5): rectseries[2].append(Rect(0, 20 * i, 20, 20))
        for i in range(5): rectseries[3].append(Rect(0, 40 * i, 40, 40))
        for i in range(3): rectseries[4].append(Rect(0, 20 * i, 40, 20))
        for i in range(3): rectseries[5].append(Rect(0, 40 * i, 20, 40))
        for i in range(10): rectseries[6].append(Rect(0, 20 * i, 20 * (i + 1), 20))
        for i in range(10): rectseries[7].append(Rect(20 * i, 0, 20, 20 * (i + 1)))

        # 0～4: 2×1型(横). 5～9: 1×2型(縦). 10～14: 1×1型. 15～19: 2×2型.
        # 20～22: 1×2型(ハートと強いブロック). 23～25: その縦バージョン.
        # 26～35: 壊せないブロック(横) 36～45: 壊せないブロック(縦).
        # 20～25はクリア条件に寄与しない。以上。
        for i in range(8):
            block.images += self.create_images("blockimages" + str(i + 1), rectseries[i])

        # 上部、両サイド(46と47)は別立て。
        surface = self.load_image("blockupper")
        block.images.append(surface)
        surface = self.load_image("blockside")
        block.images.append(surface)

        # ボールは別立て。
        imageList = self.load_image("ballimages", True)
        for i in range(2):
            surface = pygame.Surface((16, 16))
            surface.blit(imageList, (0, 0), (16 * i, 0, 16, 16))
            ball.images.append(surface)

        # 発射方向のポインターも別立て。
        self.dirimage = self.load_image("pointerimage")

        # パドル、テキスト、数字、ステージ選択、難易度。
        rectseries = []
        for i in range(5): rectseries.append([])
        # パドルは0～3が通常時、4～7が強化時。
        widths = [80, 60, 40, 30]
        for i in range(8): rectseries[0].append(Rect(0, 5 * i, widths[i % 4], 5))

        widths = [160, 340, 80, 80, 200, 120, 280, 165, 95, 145, 180, 370, 85, 240]
        for i in range(14): rectseries[1].append(Rect(0, 30 * i, widths[i], 30))

        for i in range(11): rectseries[2].append(Rect(18 * i, 0, 18, 30))

        widths = [65, 130, 180, 180, 180, 180, 180]
        for i in range(14):
            rectseries[3].append(Rect(0, 30 * i, widths[i % 7], 30))

        widths = [145, 65, 100, 65, 85]
        for i in range(10):
            rectseries[4].append(Rect(0, 30 * i, widths[i % 5], 30))

        paddle.images += self.create_images("paddleimages", rectseries[0])
        GameState.texts += self.create_images("TEXTS", rectseries[1])
        GameState.numbers += self.create_images("NUMBERS", rectseries[2])
        GameState.choices += self.create_images("CHOICES", rectseries[3])
        GameState.difficulty += self.create_images("SELECTDIFF", rectseries[4])


    def create_images(self, filename, RectList):
        """データをもとにイメージ配列を作成"""
        imageList = self.load_image(filename)
        images = []
        for rect in RectList:
            surface = pygame.Surface(rect.size)
            surface.blit(imageList, (0, 0), rect)
            images.append(surface)
        return images

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
        block((20, 40), 46)  # 天井の壁
        block((0, 40), 47); block((460, 40), 47)  # 両サイドの壁

        if self.state.stage % 5 == 1:
            # 最初だけ。パドルとボールを作る。
            self.paddle = paddle((200, 395), PADDLE_TYPE[self.state.mode])
            self.ball = ball((200, 379), self.blocks, self.paddle, MAX_LIFE[self.state.mode])
            self.state.life_image_update(self.ball.life)    # ライフ画像の初期化

        # パドルとボールのリセット
        self.paddle.rect.topleft = (200, 395)
        self.ball.rect.centerx = self.paddle.rect.centerx
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
            elif event.type == MOUSEBUTTONDOWN:
                if not self.state.mState == PLAY: return  # マウスのイベントはPLAY時のもののみ。
                self.mousedown_event(event.button)

    def keydown_event(self, key):
        if key == K_ESCAPE:
            self.state.write_data()   # データの書き込み(セーブ)
            pygame.quit()
            sys.exit()

        to_reset = self.state.keydown_events(key)  # ここでなんか返す
        if to_reset:
            self.reset()

        # ALLCLEARのときに1回だけボーナス追加。
        if self.state.mState == ALLCLEAR and self.ball.life > 0:
            bonus = self.add_bonus()
            # ここでGameStateにスコアデータを更新してもらう。
            self.state.hi_score_update(bonus, self.score)

    def mousedown_event(self, button):
        if button == 3 and self.ball.set_on:
            # 右クリックでボール発射
            dx = cos(radians(direction[self.frame // 32]))
            dy = sin(radians(direction[self.frame // 32]))
            self.ball.fpvx = 0.1 * floor(dx * self.ball.speed * 10)
            self.ball.fpvy = 0.1 * floor(dy * self.ball.speed * 10)
            self.frame = 0
            self.ball.set_on = False  # ボールがパドルから離れる
        elif button == 2 and not self.ball.set_on:
            # ボールが離れてる時中央クリックでポーズ
            self.state.mState = PAUSE

    def reset(self):
        self.state.mState = TITLE

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
            if self.kind < 10: return dmg  # 1が100, 2が250.
            elif self.kind < 15: return 3 + dmg # 4が150, 5が400.
            else: return 5 + dmg # 6が50, 7が100のパス。大きいので低スコア。
        else:
            # ピンクのブロック(100)
            if self.kind == 20 or self.kind == 23: self.tough = 0; return 1
            # 緑のブロック(500)
            if self.kind == 21 or self.kind == 24:
                if dmg > 1: self.tough = 0; return 3
                else: return 0
            # 黄緑のブロック(→緑)(500)
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
    def __init__(self, pos, kind):
        self.kind = kind  # 0, 1, 2, 3がある(EASY, NORMAL, HARD, CLAZY).
        self.image = self.images[self.kind]  # 難易度によってパドル長が変化する。
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.vx = 0
        self.ballpos = -1 # 衝突判定用
        self.far = False  # ボールが遠くにあるときに判定しない
        self.count = 0    # 40～0の範囲で動く、40～32のときに赤く光る

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        mouse_pressed = pygame.mouse.get_pressed()
    
        # カウントは40～0で、40～32のときに光ってる感じ。
        if mouse_pressed[0] and self.count == 0:
            self.count = 40
            self.image = self.images[self.kind + 4]
        if self.count > 0:
            self.count -= 1
            if self.count < 32: self.image = self.images[self.kind]

        self.rect.centerx = pygame.mouse.get_pos()[0]

        if self.rect.left< 20: self.rect.left = 20
        if self.rect.right > SCR_W - 20: self.rect.right = SCR_W - 20

class ball:
    r = 8
    speed = 4.0  # スピードアップ時は6.0にする。クラス変数は変更可能。
    images = []
    def __init__(self, pos, blocks, paddle, maxlife):
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
        self.life = maxlife   # maxlife回落ちたら終了(3, 5, 10, 12).

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.set_on:
            self.rect.x = self.paddle.rect.x + self.paddle.rect.width // 2 - self.r
            self.rect.y = self.paddle.rect.y - self.rect.height
            self.fpx = float(self.rect.x)
            self.fpy = float(self.rect.y)
            return 0  # ここ。Noneになってしまうよ。
        
        # ブロック, リフトと衝突判定
        # 1. farなのはスルー。2. 移動後の座標で衝突しないものはスルー。
        # 3. 衝突するならフラグに従って、偶数フラグなら値により速度反転、
        # 奇数フラグ(角っちょ)の場合は当たり方によって方向をいじる感じ。

        # パドルと衝突判定（パドルが先）
        self.collidepaddle()
        # ブロックと衝突判定（ダメージを記録）
        dmg = self.collideblock()              

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
            if self.paddle.count & 32 and self.count == 0:  # 強化(複数回強化しないよう修正)
                self.count = 300; self.speed = 6.0;
                self.fpvx = floor(self.fpvx * 15) * 0.1
                self.fpvy = floor(self.fpvy * 15) * 0.1
                self.image = self.images[1]
            return
        # 薄くなったので「横から当たるとき」はスルーで。
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
    choices = []  # 選択肢関係のテキスト
    difficulty = []  # 難易度選択のテキスト
    EASY, NORMAL, HARD, CLAZY = [0, 1, 2, 3]  # 難易度。
    def __init__(self):
        self.mState = TITLE
        # fontはexe化の際に障害となるので注意
        self.cursol = 0
        self.stage = 1
        self.mode = self.EASY  # デフォルト。

        self.life_image = []     # ステータスバーに表示する残りライフの画像。
        for i in range(2):
            self.life_image.append(self.numbers[0])
        self.score_image = []    # ステータスバーに表示するスコアの画像。
        for i in range(6):
            self.score_image.append(self.numbers[0])

        self.backup = []  # 解放状況、ハイスコア、フラグ。
        self.read_data()  # textデータ読み込み
        self.limit = 0    # 解放状況、たとえば2なら1～10まで。
        # バックアップデータをもとに解放状況を計算。
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

        self.rc = 0  # ・・・・？？？？

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
            screen.blit(self.texts[0], (160, 120))  # TITLE
            screen.blit(self.texts[1], (70, 180))  # PRESS ENTER KEY
            if self.rc == 5:
                screen.blit(self.texts[13], (120, 270))  # SCORE ALL RESET

        elif self.mState == SELECT:
            # 選択しているところは黒文字
            index = [i + 1 for i in range(6)]
            index[self.cursol] += 7  # 黒文字

            screen.blit(self.choices[index[0]], (80, 70))
            screen.blit(self.texts[9], (280, 70))  # Hi-SCORE

            for i in range(self.limit):
                screen.blit(self.choices[index[i + 1]], (80, 130 + 40 * i))
                for k in range(6):  # ハイスコア表示できるようにしてみた。
                    screen.blit(self.score_board[i][5 - k], (303 + 18 * k, 130 + 40 * i))
                if self.backup[i] == 3:
                    screen.blit(self.numbers[10], (60, 130 + 40 * i))
            # あとは、0なら表示しない、それと、3なら*をつける、かな・・

        elif self.mState == MODE:
            # カーソルが0から3まで動く（バックアップの初めの5つがすべて3なら4まで）
            # backupの11番に0とか1を入れてそこで判断する。
            index = [i for i in range(5)]
            index[self.cursol] += 5  # 黒文字または白の地
            for i in range(4):
                screen.blit(self.difficulty[index[i]], (165, 100 + 40 * i))
            if self.backup[10] == 1:
                screen.blit(self.difficulty[index[4]], (165, 260))

        elif self.mState == START:
            screen.blit(self.texts[2], (173, 170))  # STAGE
            screen.blit(self.numbers[self.stage // 10], (271, 170))
            screen.blit(self.numbers[self.stage % 10], (289, 170))

        elif self.mState == PAUSE:
            screen.blit(self.texts[3], (200, 120))  # PAUSE

            index = [0, 1]
            index[self.cursol] += 7  # 黒文字
            screen.blit(self.choices[index[0]], (200, 180))
            screen.blit(self.choices[index[1]], (200, 220))

        elif self.mState == GAMEOVER:
            screen.blit(self.texts[4], (140, 120))  # GAME OVER...
            screen.blit(self.texts[1], (70, 180))  # PRESS ENTER KEY

        elif self.mState == CLEAR:
            screen.blit(self.texts[5], (180, 120))  # CLEAR!!

            if self.stage % 5 == 0:
                screen.blit(self.texts[6], (100, 180))  # STAGE ALL CLEAR!!
            screen.blit(self.texts[1], (70, 240))  # PRESS ENTER KEY

        elif self.mState == ALLCLEAR:
            screen.blit(self.texts[7], (100, 100))  # LIFE BONUS
            screen.blit(self.texts[8], (100, 140))  # SCORE
            screen.blit(self.texts[9], (100, 180))  # Hi-SCORE
            if self.backup[11] == 1:
                screen.blit(self.texts[11], (55, 220))  # Hi-SCORE UPDATE!!
            screen.blit(self.texts[1], (70, 260))  # PRESS ENTER KEY
            for i in range(5):
                screen.blit(self.score_board[5][4 - i], (270 + 18 * i, 100))
            for i in range(6):
                screen.blit(self.score_image[5 - i], (200 + 18 * i, 140))
            x = self.stage // 5 - 1
            for i in range(6):
                screen.blit(self.score_board[x][5 - i], (250 + 18 * i, 180))

    def keydown_events(self, key):
        if self.mState == TITLE:
            if key == K_RETURN:
                self.mState = SELECT
                self.rc = 0  # 元に戻す。
            else:
                if self.backup[10] == 0: return False
                self.calc_resetcount(key)   # 10番フラグが立ってる時のみ。
            return False

        elif self.mState == SELECT:
            if key == K_DOWN:
                self.cursol = (self.cursol + 1) % (self.limit + 1); return False

            elif key == K_UP:
                if self.cursol > 0:
                    self.cursol = (self.cursol + self.limit) % (self.limit + 1)
                else:
                    self.cursol = self.limit
                return False
                
            elif key == K_RETURN:
                if self.cursol == 0:
                    self.mState = TITLE; return True
                else:
                    self.mState = MODE
                    self.stage = (self.cursol * 5) - 4
                    self.cursol = 0
                return False

        elif self.mState == MODE:
            if key == K_DOWN:
                self.cursol += 1
                if self.cursol > 3 + self.backup[10]: self.cursol = 0
            elif key == K_UP:
                self.cursol -= 1
                if self.cursol < 0: self.cursol = 3 + self.backup[10]
            elif key == K_RETURN:
                if self.cursol == 0:
                    self.mState = SELECT
                    return False
                else:
                    self.mState = START
                    self.mode = self.cursol - 1  # 1, 2, 3, 4のときEASY, NORMAL, HARD, CLAZY.
                    self.cursol = 0
            return False

        elif self.mState == PAUSE:
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

        elif self.mState == CLEAR:
            if key == K_RETURN:
                self.stage += 1
                if self.stage % 5 == 1:  # 6, 11, ...の時にリセット。
                    self.mState = ALLCLEAR
                    # 次のステージに行けるようにする。
                    return False  # stageはこっちで1に戻す感じ。
                else:
                    self.mState = START; return False
        # ALLCLEARからENTERキー押してTITLEに戻るのでここはFalseで。

        elif self.mState == ALLCLEAR:
            if key == K_RETURN:
                self.mState = TITLE
                # ここでステージの解放、及び、
                # 3 3 3 3でかつ0なら1にする処理を挟む。
                # すべて3なら10番にフラグを立てる。→CRAZYモード、エディタ、スコアリセット。
                x = self.stage // 5
                if x < 4 and self.backup[x] == 0:
                    self.backup[x] = 1 # 次のステージ組解放
                    self.limit += 1
                if self.mode == self.HARD:
                    self.backup[x - 1] = 3  # とにかくHARDでクリアしたら3を立てる。
                if self.backup[4] == 0 and self.backup[0] + self.backup[1] + self.backup[2] + self.backup[3] == 12:
                    self.backup[4] = 1  # EXTRA解放
                    self.limit = 5      # limitをMAXに。
                if self.backup[4] == 3 and self.backup[10] == 0:
                    self.backup[10] = 1   # いろいろ解放される（CRAZYとかエディタとか）。
                self.backup[11] = 0  # フラグを消す。
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
        # 始めの5つは0, 1, 3で、その後の5つがスコア。
        # あと、11番目は3が5つ並んだ時に0から1にする（CLAZY解禁状況）。
        # 12番目はハイスコアを更新するとき1になるフラグ用。
        for i in range(11): self.backup.append(int(data[i]))
        self.backup.append(0)

    def write_data(self):
        # データの書き込み
        filename = os.path.join("stages", "scores.txt")
        fp = open(filename, "w")
        fp.write(str(self.backup[0]))
        for i in range(1, 11):
            fp.write(" " + str(self.backup[i]))
        fp.close()

    def hi_score_update(self, bonus, score):
        # ここで全部やる。(0)bonus画像設定、さらにscore(最終スコア)と
        # stageから分かるそのステージ組のハイスコアを比べて上がるようなら
        # (1)ハイスコアbackupの更新、(2)表示画像の更新、
        # (3)HARDでクリアしたら星を付ける。（スコアは無関係）
        # (4)ハイスコア更新したらフラグ立ててALLCLEAR画面にあれする。
        for i in range(5):
            self.score_board[5][i] = self.numbers[bonus % 10]
            bonus //= 10
        x = self.stage // 5 - 1   # 現在のステージ組の番号（0～4）
        if score > self.backup[5 + x]:
            self.backup[5 + x] = score
            for i in range(6):
                self.score_board[x][i] = self.numbers[score % 10]
                score //= 10
            self.backup[11] = 1  # フラグ。テキスト表示用。

    def calc_resetcount(self, key):
        # 一定の条件下でrcを進めていく。
        if self.rc == 0 and key == K_UP: self.rc += 1; return
        if self.rc == 1 and key == K_DOWN: self.rc += 1; return
        if self.rc == 2 and key == K_RIGHT: self.rc += 1; return
        if self.rc == 3 and key == K_LEFT: self.rc += 1; return
        if self.rc == 4 and key == K_SPACE:
            self.rc += 1
            self.hi_score_allreset()
            return

    def hi_score_allreset(self):
        # ハイスコアデータ全消去
        for i in range(5):
            for j in range(6):
                self.score_board[i][j] = self.numbers[0]
            self.backup[5 + i] = 0
        self.write_data()

if __name__ =="__main__":
    Play()
