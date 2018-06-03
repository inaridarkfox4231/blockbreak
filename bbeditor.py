
import pygame
from pygame.locals import *
import sys
import os

SCR_RECT = Rect(0, 0, 440, 320)
GS = 20  # グリッドサイズ

width = 22
height = 13

keyList = [K_a, K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m,
        K_n, K_o, K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x, K_y, K_z]

CAN_BREAK, CANNOT_BREAK = [0, 1]

class editor():
    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode(SCR_RECT.size)
        pygame.display.set_caption("editor")

        self.blocks = pygame.sprite.RenderUpdates()
        block.containers = self.blocks
        self.mode = CAN_BREAK   # 壊せるブロックとそうでないブロック

        self.stagemap = []  # ステージマップ。
        self.occupy = []     # 1と0で占有状況を示す感じ。
        for i in range(13):
            line = []
            for j in range(22): line.append('.') 
            self.stagemap.append(line)
            line = []
            for j in range(22): line.append(0)
            self.occupy.append(line)

        self.loading()
        clock = pygame.time.Clock()

        while True:
            screen.blit(self.backImg, (0, 0))
            self.blocks.draw(screen)
            pygame.display.update()
            self.key_handler()

    def loading(self):
        """背景、ブロック画像のロード"""
        self.backImg = self.load_image("editor_bg")
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

        # 壊せる20～22の1×2型。1UP, 緑、黄緑。
        imageList = self.load_image("blockimages5")
        for i in range(3):
            surface = pygame.Surface((40, 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 40, 20))
            block.images.append(surface)

        # 23～25で縦型も用意したい。1UP, 緑、黄緑。
        imageList = self.load_image("blockimages6")
        for i in range(3):
            surface = pygame.Surface((20, 40))
            surface.blit(imageList, (0, 0), (0, 40 * i, 20, 40))
            block.images.append(surface)

        # 壊せないブロック26～35（横型、長さは1～10）
        imageList = self.load_image("blockimages7")
        for i in range(10):
            surface = pygame.Surface((20 * (i + 1), 20))
            surface.blit(imageList, (0, 0), (0, 20 * i, 20 * (i + 1), 20))
            block.images.append(surface)

        # 壊せないブロック36～45（縦型、長さは1～10）
        imageList = self.load_image("blockimages8")
        for i in range(10):
            surface = pygame.Surface((20, 20 * (i + 1)))
            surface.blit(imageList, (0, 0), (20 * i, 0, 20, 20 * (i + 1)))
            block.images.append(surface)

    def key_handler(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                self.keydown_event(event.key)

    def keydown_event(self, key):
        """キーイベント"""
        if key == K_ESCAPE:
            pygame.quit()
            sys.exit()
        elif key == K_LCTRL:
            # ブロックの種類の切り替え
            if self.mode == CANNOT_BREAK: self.mode = CAN_BREAK
            else: self.mode = CANNOT_BREAK
        elif key == K_RETURN:
            # マップの保存
            self.save()
            self.map_init()   # 初期化
            self.blocks.empty()  # 初期化
        else:
            x, y = pygame.mouse.get_pos()
            x = x // GS; y = y // GS
            if key == K_DELETE:
                self.delete_block((x, y))
            else:
                kind = self.calc_kind(key) # 0～47のうち該当するやつを返す
                # なければ-1が返るのでブロックは作れない。
                if kind >= 0:
                    self.add_block((x, y), kind)
    
    def map_init(self):
        """マップデータの初期化"""
        for i in range(13):
            for j in range(22):
                self.stagemap[i][j] = '.'

    def calc_kind(self, key):
        """keyの値に応じてブロックのkindを返す"""
        if not key in keyList: return -1
        else:
            if self.mode == CAN_BREAK:
                return int(key) - 97
            else:
                if int(key) < 117: return int(key) - 97 + 26
        return -1

    def calc_occupy(self, pos, kind):
        """占有するマスの情報を与える"""
        occupied = []
        occupied.append(pos)
        x, y = pos
        if kind < 5:
            occupied.append((x + 1, y))
        elif kind < 10:
            occupied.append((x, y + 1))
        elif kind < 15: pass
        elif kind < 20:
            occupied.append((x, y + 1)); occupied.append((x + 1, y))
            occupied.append((x + 1, y + 1))
        elif kind < 23:
            occupied.append((x + 1, y))
        elif kind < 26:
            occupied.append((x, y + 1))
        elif kind < 36:
            for k in range(1, kind - 25):
                occupied.append((x + k, y))
        elif kind < 46:
            for k in range(1, kind - 35):
                occupied.append((x, y + k))
        else:
            return None
        # はみ出しチェック
        for o_pos in occupied:
            x, y = o_pos
            if x < 0 or y < 0 or x >= width or y >= height: return None
        return occupied
        # とりあえずはみ出すかどうかだけここで調べちゃう。でないと
        # インデックスエラーになってしまうので。エラー処理でもいいけど。

    def add_block(self, pos, kind):
        """ブロックの追加"""
        occupied = self.calc_occupy(pos, kind)
        if occupied == None: return
        for o_pos in occupied:
            x, y = o_pos
            if self.occupy[y][x] == 1: return  # 占有されていたらNG.
        # ブロックを作る。
        block(pos, kind)
        for o_pos in occupied:
            x, y = o_pos
            self.occupy[y][x] = 1
        if kind < 26:
            self.stagemap[y][x] = chr(kind + 65)
        else:
            self.stagemap[y][x] = chr(kind - 26 + 97)

    def delete_block(self, pos):
        """ブロックの削除"""
        for block in self.blocks:
            if block.pos == pos:
                self.stagemap[pos[1]][pos[0]] = '.'
                occupied = self.calc_occupy(pos, block.kind)
                for o_pos in occupied:
                    x, y = o_pos
                    self.occupy[y][x] = 0
                block.kill()
                break

    def load_image(self, filename):
        """画像のロード"""
        filename += ".png"
        filename = os.path.join("images", filename)
        image = pygame.image.load(filename).convert()
        return image

    def save(self): pass
        """ファイルに保存する"""
        # 頭にフォルダ名/ってつけるとcdのフォルダ内に入るのでそうして。

class block(pygame.sprite.Sprite):
    """ブロックの定義"""
    images = []
    def __init__(self, pos, kind):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.kind = kind # A～Zとa～tのアルファベットの数字評価。
        self.pos = pos   # posは整数指定
        self.image = self.images[self.kind]
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos[0] * GS, pos[1] * GS)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

if __name__ == "__main__":
    editor()
"""
    posと押されたキーの組み合わせに対して
    ブロックの種類、占有マスが計算され、
    占有マスに'.'でないものがあったらFalse(何も起きない).
    はみ出す場合も却下。でなければ、
    posに'なんか'が記入されてblocksに入る（入るのは生成すれば勝手に入る）。
    取り消すには、K_DELETE押す。そのとき、posに対するところが
    '.'なら何も起きない。でなければそこを'.'にして、かつ該当する
    posをもつブロックをblocksから（一意に定まる）みつけてあればkillする。
    最後に、ファイルの生成。mapmaker_0.pyのメソッドを使う。
    さらに、ファイルの名前を入力するとき.mapで終わってないとエラーが出るようにする。
    そして、保存が終わったらデータを初期化してエディタ画面に戻る。
    最後に、画面の下の方にESCAPEで終了とかエンターキーで保存とか書いとけ。
    コントロールキー押すと入れ替わる。
    あ、そうだ、os.path.existsで存在するファイル名かどうか調べて、
    無い時だけ作るのを忘れずに。
"""
