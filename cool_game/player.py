import cocos
import pyglet

from cocos.actions import Move
from pyglet.window import key
from pyglet import clock


import cocos.collision_model as cm

import sprites_loader
from collisions_managers import PLAYER_WALL_COLLISION_MANAGER
from collisions_managers import PLAYER_WATER_COLLISION_MANAGER


class PlayerMove(Move):

    def step(self, dt):
        x, y = self.target.position
        old_x, old_y = x, y

        dx, dy = self.target.velocity
        ddx, ddy = getattr(self.target, 'acceleration', (0, 0))
        gravity = getattr(self.target, 'gravity', 0)
        dx += ddx * dt
        dy += (ddy + gravity) * dt
        self.target.velocity = (dx, dy)
        x += dx * dt
        y += dy * dt

        i = 0
        while i < 4:
            self.target.cshape.center = x, self.target.cshape.center[1]
            collisions = PLAYER_WALL_COLLISION_MANAGER.objs_colliding(self.target)
            if collisions:
                self.target.cshape.center = old_x, self.target.cshape.center[1]
                if x < old_x:
                    x = x + (old_x - x) // 4
                else:
                    x = x - (x - old_x) // 4

                i += 1
                continue
            break
        else:
            self.target.cshape.center = old_x, self.target.cshape.center[1]
            x = old_x

        i = 0
        while i < 4:
            self.target.cshape.center = self.target.cshape.center[0], y
            collisions = PLAYER_WALL_COLLISION_MANAGER.objs_colliding(self.target)
            if collisions:
                self.target.cshape.center = self.target.cshape.center[0], old_y
                if x < old_x:
                    y = y + (old_y - y) // 4
                else:
                    y = y - (y - old_y) // 4
                i += 1
                continue
            break
        else:
            self.target.cshape.center = self.target.cshape.center[0], old_y
            y = old_y

        self.target.position = (x, y)
        dr = getattr(self.target, 'dr', 0)
        ddr = getattr(self.target, 'ddr', 0)
        if dr or ddr:
            dr = self.target.dr = dr + ddr*dt
        if dr:
            self.target.rotation += dr * dt


class Player(cocos.cocosnode.CocosNode):
    def __init__(self):
        super().__init__()

        player_tiles = sprites_loader.PlayerTiles()
        self.down = cocos.sprite.Sprite(pyglet.image.Animation.from_image_sequence(player_tiles.down, 0.2))
        self.left = cocos.sprite.Sprite(pyglet.image.Animation.from_image_sequence(player_tiles.left, 0.2))
        self.right = cocos.sprite.Sprite(pyglet.image.Animation.from_image_sequence(player_tiles.left, 0.2))
        self.up = cocos.sprite.Sprite(pyglet.image.Animation.from_image_sequence(player_tiles.up, 0.2))

        self.right.scale_x = -1

        self.down.opacity = 1
        self.left.opacity = 0
        self.right.opacity = 0
        self.up.opacity = 0

        self.add(self.down)
        self.add(self.left)
        self.add(self.right)
        self.add(self.up)

    def switch_face(self, face):
        if face == 'down':
            self.down.opacity = 255
            self.left.opacity = 0
            self.right.opacity = 0
            self.up.opacity = 0
        elif face == 'left':
            self.down.opacity = 0
            self.left.opacity = 255
            self.right.opacity = 0
            self.up.opacity = 0
        elif face == 'right':
            self.down.opacity = 0
            self.left.opacity = 0
            self.right.opacity = 255
            self.up.opacity = 0
        else:
            self.down.opacity = 0
            self.left.opacity = 0
            self.right.opacity = 0
            self.up.opacity = 255


class PlayerLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True
    _pos_offset = 24
    _tile_size = 48, 48

    def __init__(self, start_point):
        super().__init__()

        self._reversed = False

        self.c_face = 'down'
        self.face = self.c_face
        self.player = Player()
        self.player.position = start_point

        self.player.velocity = 0, 0
        # self.player.movement_precision = 16 * 1.5
        self.player.movement_precision = 16 * 1.5 * 3
        self.player.speed = 160 * 1.5

        self.player.cshape = cm.AARectShape(
            self.player.position,
            48//8,
            48//8
        )

        self.add(self.player)
        PLAYER_WALL_COLLISION_MANAGER.add(self.player)
        PLAYER_WATER_COLLISION_MANAGER.add(self.player)

        self.player.do(PlayerMove())

        self.schedule(self.update)

    def update(self, dt):
        self.player.cshape.center = self.player.position
        x, y = self.player.velocity
        speed_kf = 1

        diag = False
        if x != 0 and y != 0:
            diag = True
        collisions = PLAYER_WATER_COLLISION_MANAGER.objs_colliding(self.player)
        if collisions:
            speed_kf = 0.33

        if diag:
            speed_kf = 0.66
            if collisions:
                speed_kf = 0.25

        self.player.movement_precision = (
            (self.player.speed * speed_kf) / (clock.get_fps() or 60)
        ) * ((clock.get_fps() or 60) / 10) * 3

        if x != 0:
            x = self.player.movement_precision * (-1 if x < 0 else 1)

        if y != 0:
            y = self.player.movement_precision * (-1 if y < 0 else 1)

        self.player.velocity = x, y

        if self.face != self.c_face:
            self.player.switch_face(self.face)
            self.c_face = self.face

    def on_key_press(self, symbol, modifiers):
        # print(symbol)
        if symbol == key.A:
            self.player.velocity = -self.player.movement_precision, self.player.velocity[1]
        elif symbol == key.D:
            self.player.velocity = self.player.movement_precision, self.player.velocity[1]
        elif symbol == key.W:
            self.player.velocity = self.player.velocity[0], self.player.movement_precision
        elif symbol == key.S:
            self.player.velocity = self.player.velocity[0], -self.player.movement_precision

    def on_key_release(self, symbol, modifiers):
        # print(symbol)
        if symbol == key.A:
            self.player.velocity = 0, self.player.velocity[1]
        elif symbol == key.D:
            self.player.velocity = 0, self.player.velocity[1]
        elif symbol == key.W:
            self.player.velocity = self.player.velocity[0], 0
        elif symbol == key.S:
            self.player.velocity = self.player.velocity[0], 0

    def on_mouse_motion(self, x, y, dx, dy):
        """Called when the mouse moves over the app window with no button pressed

        (x, y) are the physical coordinates of the mouse
        (dx, dy) is the distance vector covered by the mouse pointer since the
          last call.
        """
        player_x, player_y = self.player.world_size[0] / 2, self.player.world_size[1] / 2
        # print(x, y)

        if player_x > x:
            pos_x = 'right'
            pos_x_diff = player_x - x
        else:
            pos_x = 'left'
            pos_x_diff = x - player_x

        if player_y > y:
            pos_y = 'down'
            pos_y_diff = player_y - y
        else:
            pos_y = 'up'
            pos_y_diff = y - player_y

        self.face = pos_x if pos_x_diff >= pos_y_diff else pos_y