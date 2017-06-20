"""
Cocos Invaders: A Space Invaders clone in Python, using the Cocos2d framework.

"""
import cocos.layer
import cocos.sprite
import cocos.collision_model as cm
import cocos.euclid as eu
import random

from collections import defaultdict
from pyglet.window import key
from pyglet.image import load, ImageGrid, Animation


class Actor(cocos.sprite.Sprite):
    """
    The Actor class represent all player and non-player actors in the game.
    """
    def __init__(self, image, x, y):
        super(Actor, self).__init__(image)
        self.position = eu.Vector2(x, y)
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)

    def move(self, offset):
        """
        Moves the actor.
        :param offset:
        :return:
        """
        self.position += offset
        self.cshape.center += offset

    def update(self, elapsed):
        pass

    def collide(self, other):
        pass


class PlayerCannon(Actor):
    """
    Player controlled actor behavior.
    """
    KEYS_PRESSED = defaultdict(int)

    def __init__(self, x, y):
        super(PlayerCannon, self).__init__('images/cannon.png', x, y)
        self.speed = eu.Vector2(200, 0)

    def update(self, elapsed):
        pressed = PlayerCannon.KEYS_PRESSED
        space_pressed = pressed[key.SPACE] == 1
        if PlayerShoot.INSTANCE is None and space_pressed:
            self.parent.add(PlayerShoot(self.x, self.y + 50))

        movement = pressed[key.RIGHT] - pressed[key.LEFT]
        if movement != 0:
            self.move(self.speed * movement * elapsed)

        w = self.width * 0.5
        if movement != 0 and w <= self.x <= self.parent.width - w:
            self.move(self.speed * movement * elapsed)

    def collide(self, other):
        other.kill()
        self.kill()


class GameLayer(cocos.layer.Layer):
    """
    Keeps track of player lives left and current score.
    Handles input key events.
    Creates the game actors and adds them as child nodes.
    Runs the game loop by executing a scheduled function for each frame where the collisions are processed and
    the object positions are updated.
    """
    is_event_handler = True

    def on_key_press(self, k, _):
        PlayerCannon.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        PlayerCannon.KEYS_PRESSED[k] = 0

    def __init__(self, hud):
        super(GameLayer, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.hud = hud
        self.width = w
        self.height = h
        self.lives = 3
        self.score = 0
        self.update_score()
        self.create_player()
        self.create_alien_group(100, 300)
        cell = 1.25 * 50
        self.collman = cm.CollisionManagerGrid(0, w, 0, h,
                                               cell, cell)
        self.schedule(self.update)

    def create_player(self):
        """
        :return: Creates a PlayerCannon object in the center of the screen.
        """
        self.player = PlayerCannon(self.width * 0.5, 50)
        self.add(self.player)
        self.hud.update_lives(self.lives)

    def update_score(self, score=0):
        """
        Increments score for each alien destroyed.
        :param score: Initial score value is 0.
        :return:
        """
        self.score += score
        self.hud.update_score(self.score)

    def create_alien_group(self, x, y):
        """
        Initializes the rows of descending aliens by creating a new alien group and adding all enemies to the layer as
        child nodes.
        :param x: x coordinate
        :param y: y coordinate
        :return:
        """
        self.alien_group = AlienGroup(x, y)
        for alien in self.alien_group:
            self.add(alien)

    def update(self, dt):
        """
        Callback method that will be scheduled for execution each frame.
        :param dt: DeltaTime value.
        :return:
        """
        self.collman.clear()
        for _, node in self.children:
            self.collman.add(node)
            if not self.collman.knows(node):
                self.remove(node)

        self.collide(PlayerShoot.INSTANCE)
        if self.collide(self.player):
            self.respawn_player()
        for column in self.alien_group.columns:
            shoot = column.shoot()
            if shoot is not None:
                self.add(shoot)

        for _, node in self.children:
            node.update(dt)
        self.alien_group.update(dt)

        if random.random() < 0.001:
            self.add(MysteryShip(50, self.height - 50))

    def collide(self, node):
        """
        Encapsulates the call to iter_colliding and checks if the node is a reference to a valid object.
        :param node:
        :return:
        """
        if node is not None:
            for other in self.collman.iter_colliding(node):
                node.collide(other)
                return True
        return False

    def respawn_player(self):
        """
        Updates player lives and respawns player by calling create_player() while there are more than 0 lives left.
        Stops gameplay by unscheduling update when there are no lives left.
        :return:
        """
        self.lives -= 1
        if self.lives < 0:
            self.unschedule(self.update)
            self.hud.show_game_over()
        else:
            self.create_player()


class HUD(cocos.layer.Layer):
    """
    Heads Up Display class. Holds current score and number of lives left.
    """
    def __init__(self):
        super(HUD, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.score_text = cocos.text.Label('', font_size=18)
        self.score_text.position = (20, h - 40)
        self.lives_text = cocos.text.Label('', font_size=18)
        self.lives_text.position = (w - 100, h - 40)
        self.add(self.score_text)
        self.add(self.lives_text)


    def update_score(self, score):
        self.score_text.element.text = 'Score: %s' % score

    def update_lives(self, lives):
        self.lives_text.element.text = 'Lives: %s' % lives

    def show_game_over(self):
        w, h = cocos.director.director.get_window_size()
        game_over = cocos.text.Label('Game Over', font_size=50, anchor_x='center', anchor_y='center')
        game_over.position = w * 0.5, h * 0.5
        self.add(game_over)


class Alien(Actor):
    """
    Non player character behavior.
    """
    def load_animation(image):
        seq = ImageGrid(load(image), 2, 1)
        return Animation.from_image_sequence(seq, 0.5)

    TYPES = {
        '1': (load_animation('images/alien1.png'), 40),
        '2': (load_animation('images/alien2.png'), 20),
        '3': (load_animation('images/alien3.png'), 10)
    }

    def from_type(x, y, alien_type, column):
        animation, score = Alien.TYPES[alien_type]
        return Alien(animation, x, y, score, column)

    def __init__(self, img, x, y, score, column=None):
        super(Alien, self).__init__(img, x, y)
        self.score = score
        self.column = column

    def on_exit(self):
        super(Alien, self).on_exit()
        if self.column:
            self.column.remove(self)


class MysteryShip(Alien):
    """
    Mysterious ship that appears randomly at top of screen.
    """
    SCORES = [10, 50, 100, 200]

    def __init__(self, x, y):
        score = random.choice(MysteryShip.SCORES)
        super(MysteryShip, self).__init__('images/alien4.png', x, y, score)
        self.speed = eu.Vector2(150, 0)

    def update(self, elapsed):
        self.move(self.speed * elapsed)


class AlienColumn(object):
    def __init__(self, x, y):
        alien_types = enumerate(['3', '3', '2', '2', '1'])
        self.aliens = [Alien.from_type(x, y+i*60, alien, self)
                       for i, alien in alien_types]

    def should_turn(self, d):
        """
        Checks if the column has reached the side of the screen in current direction.
        :returns False if there are no aliens left in the column.
        """
        if len(self.aliens) == 0:
            return False
        alien = self.aliens[0]
        x, width = alien.x, alien.parent.width
        return x >= width - 50 and d == 1 or x < 50 and d == -1

    def remove(self, alien):
        self.aliens.remove(alien)

    def shoot(self):
        if random.random() < 0.001 and len(self.aliens) > 0:
            pos = self.aliens[0].position
            return Shoot(pos[0], pos[1] - 50)
        return None


class AlienGroup(object):
    def __init__(self, x, y):
        self.columns = [AlienColumn(x + i * 60, y)
                        for i in range(10)]
        self.speed = eu.Vector2(10, 0)
        self.direction = 1
        self.elapsed = 0.0
        self.period = 1.0

    def update(self, elapsed):
        """
        Sums the elapsed times between frames, and moves whole group down or sideways after a certain period.
        :param elapsed:
        :return:
        """
        self.elapsed += elapsed
        while self.elapsed >= self.period:
            self.elapsed -= self.period
            offset = self.direction * self.speed
            if self.side_reached():
                self.direction *= -1
                offset = eu.Vector2(0, -10)
            for alien in self:
                alien.move(offset)

    def side_reached(self):
        return any(map(lambda c: c.should_turn(self.direction), self.columns))

    def __iter__(self):
        """
        Lets us call for alien in alien_group in rest of code.
        :return:
        """
        for column in self.columns:
            for alien in column.aliens:
                yield alien


class Shoot(Actor):
    def __init__(self, x, y, img='images/shoot.png'):
        super(Shoot, self).__init__(img, x, y)
        self.speed = eu.Vector2(0, -400)

    def update(self, elapsed):
        self.move(self.speed * elapsed)


class PlayerShoot(Shoot):
    INSTANCE = None

    def __init__(self, x, y):
        super(PlayerShoot, self).__init__(x, y, 'images/laser.png')
        self.speed *= -1
        PlayerShoot.INSTANCE = self

    def collide(self, other):
        if isinstance(other, Alien):
            self.parent.update_score(other.score)
            other.kill()
            self.kill()

    def on_exit(self):
        super(PlayerShoot, self).on_exit()
        PlayerShoot.INSTANCE = None


if __name__ == "__main__":
    cocos.director.director.init(caption='Cocos Invaders', width=800, height=650)
    main_scene = cocos.scene.Scene()
    hud_layer = HUD()
    main_scene.add(hud_layer, z=1)
    game_layer = GameLayer(hud_layer)
    main_scene.add(game_layer, z=0)
    cocos.director.director.run(main_scene)
