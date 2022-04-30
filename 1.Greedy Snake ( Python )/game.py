from dataclasses import dataclass
import enum
import time
from typing import List, Tuple
import pygame
import random


red = (255, 0, 0)
black = (0, 0, 0)
green = (0, 255, 0)
yellow = (255, 255, 0)


@dataclass
class ColRowPoint:
    Col: int
    Row: int


class EDirection(enum.IntEnum):
    Up = 0
    Right = 1
    Down = 2
    Left = 3


class Snake:
    def __init__(self):
        self.__body: List[ColRowPoint] = []
        self.__body.append(ColRowPoint(0, 0))
        self.__body.append(ColRowPoint(1, 0))
        self.__body.append(ColRowPoint(2, 0))
        self.food: List[any] = []

    @property
    def length(self):
        return len(self.__body)

    def move_next(self, point: ColRowPoint):
        if point in self.__body:
            return False

        self.__body.append(point)

        return True

    def get_head(self) -> ColRowPoint:
        return self.__body[-1]

    def pop_tail(self) -> ColRowPoint:  # get the first element of the list
        return self.__body.pop(0)

    def eat(self, point: ColRowPoint):
        self.__body.append(point)

    def get_body(self) -> List[ColRowPoint]:
        return self.__body


class Board:
    def __init__(self, window, window_size: Tuple[int, int], pitch=40, draw_size=30, offset_x=None, offset_y=None):
        self.start_x = (pitch - draw_size) // 2
        self.start_y = self.start_x

        window_width = window_size[0]
        window_height = window_size[1]

        if offset_x:
            self.start_x += offset_x
            window_width -= offset_x

        if offset_y:
            self.start_y += offset_y
            window_height -= offset_y

        self.pitch = pitch
        self.draw_size = draw_size
        self.window = window

        max_col = window_width // pitch
        max_row = window_height // pitch
        # self._board = [[None]*max_col]*max_row
        self._board = [[None for _ in range(max_col)] for _ in range(max_row)]

    @property
    def max_col(self):
        return len(self._board[0])

    @property
    def max_row(self):
        return len(self._board)

    def is_in_region(self, point: ColRowPoint) -> bool:
        if point.Col < self.max_col and point.Col >= 0 and point.Row < self.max_row and point.Row >= 0:
            return True
        else:
            return False

    def is_food(self, point: ColRowPoint):
        return self._food_pos == point

    def get_available(self):
        result = [ColRowPoint(col, row) for row in range(self.max_row)
                  for col in range(self.max_row) if self._board[row][col] is None]

        return result

    def update_cell_state(self, point: ColRowPoint, color: Tuple[int, int, int], update_validate=True):
        col = point.Col
        row = point.Row

        x = self.start_x + col * self.pitch
        y = self.start_y + row * self.pitch

        if self._board[row][col]:
            rect = self._board[row][col]
            del rect
            self._board[row][col] = None

        rect = pygame.draw.rect(self.window, color, (x, y, self.draw_size, self.draw_size))
        self._board[row][col] = rect

        if update_validate:
            pygame.display.update()

    def gen_food(self):
        spaces = self.get_available()
        self._food_pos = spaces[random.randint(0, len(spaces)-1)]
        self.update_cell_state(self._food_pos, yellow)


class Game:
    def __init__(self):
        self.window_size = (640, 530)
        pygame.init()
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption('Greedy Snake')

        self.direction: EDirection = EDirection.Right
        self.cache_dir: EDirection = self.direction
        self.board = Board(self.window, self.window_size, offset_y=50)
        self._is_game_over: bool = False

        self.__init_snake()

        self._delay_count_list = [30, 25, 20, 15, 10, 5]
        self._level = 1

        self.board.gen_food()
        self.__score_display_rect = None
        self.update_score(0)

    def __init_snake(self):
        self.snake = Snake()

        snake_head = self.snake.get_head()
        for element in self.snake.get_body():
            is_head = element is snake_head
            if is_head:
                color = red
            else:
                color = green

            self.board.update_cell_state(element, color, is_head)

    @property
    def is_game_over(self):
        return self._is_game_over

    @property
    def delay_count(self):
        return self._delay_count_list[self._level-1]

    def change_direction(self, direction: EDirection):
        if self.direction == EDirection.Up and direction == EDirection.Down:
            return False
        elif self.direction == EDirection.Down and direction == EDirection.Up:
            return False
        elif self.direction == EDirection.Left and direction == EDirection.Right:
            return False
        elif self.direction == EDirection.Right and direction == EDirection.Left:
            return False

        self.cache_dir = direction

        return True

    def move_next(self):
        self.direction = self.cache_dir

        head = self.snake.get_head()
        next_point = ColRowPoint(head.Col, head.Row)

        if self.direction == EDirection.Up:
            next_point.Row -= 1
        elif self.direction == EDirection.Down:
            next_point.Row += 1
        elif self.direction == EDirection.Right:
            next_point.Col += 1
        elif self.direction == EDirection.Left:
            next_point.Col -= 1

        self._islock = False

        if not self.board.is_in_region(next_point):
            print('Game Over, out of range')
            self._is_game_over = True

            return False

        eat_food = self.board.is_food(next_point)

        if eat_food:
            self.snake.eat(next_point)
            level = self.snake.length // len(self._delay_count_list) + 1

            if level > len(self._delay_count_list):
                level = len(self._delay_count_list)

            self._level = level

            self.update_score((self.snake.length-3)*10)

        else:
            if not self.snake.move_next(next_point):
                print('Game Over, eat self')
                self._is_game_over = True

                return False

        self.board.update_cell_state(head, green, False)

        self.board.update_cell_state(next_point, red, False)  # new snake head

        if not eat_food:
            snake_tail = self.snake.pop_tail()  # remove snake old tail
            self.board.update_cell_state(snake_tail, black, True)
        else:
            self.board.gen_food()

        return True

    def update_score(self, score):
        if self.__score_display_rect:
            self.window.fill(black, self.__score_display_rect)
            del self.__score_display_rect
            self.__score_display_rect = None

        score_font = pygame.font.SysFont('comicsansms', 35)
        value = score_font.render(f'Your Score: {score}', True, yellow)
        rect = self.window.blit(value, [0, 0])
        self.__score_display_rect = rect

    def message(self, msg, color):
        font_style = pygame.font.SysFont(None, 50)
        mesg = font_style.render(msg, True, color)

        message_size = mesg.get_size()

        self.window.blit(mesg, [(self.window_size[0]-message_size[0])/2, (self.window_size[1]-message_size[1])/2])
        pygame.display.update()


def main():
    my_game = Game()

    count = 0

    while True:
        count %= my_game.delay_count
        if count == 0:
            if not my_game.move_next():
                break

        count += 1
        time.sleep(0.01)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.display.quit()
                
                return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    print('LEFT')
                    my_game.change_direction(EDirection.Left)
                elif event.key == pygame.K_RIGHT:
                    print('RIGHT')
                    my_game.change_direction(EDirection.Right)
                elif event.key == pygame.K_UP:
                    print('UP')
                    my_game.change_direction(EDirection.Up)
                elif event.key == pygame.K_DOWN:
                    print('DOWN')
                    my_game.change_direction(EDirection.Down)

    if my_game.is_game_over:
        my_game.message('Game Over !!!', red)
    
    # wait for close the game
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                pygame.display.quit()
                
                return


main()
