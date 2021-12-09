from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Callable, Optional

import pygame
from pygame import Color, Rect, Vector2


# TODO: It might be cool to have a global style thing.
# TODO: Add containers that layout widgets nicely
# implementing a flexbox would be *chefs kiss*


class Widget(abc.ABC):
    """
    A widget is any UI element.

    Every widget has a position and a size. At initialization a widgets
    position can be None. That means it will be assigned by a parent later.
    If it isn't then an error will be thrown when the widget is drawn.
    """

    @abc.abstractmethod
    def draw(self, screen: pygame.Surface):
        if self.pos is None:
            raise Exception('Widget cannot be drawn without a position')

    def handle(self, event: pygame.event.Event):
        pass

    @property
    @abc.abstractmethod
    def pos(self) -> Vector2:
        pass

    @pos.setter
    @abc.abstractmethod
    def pos(self, pos: Vector2):
        pass

    @property
    @abc.abstractmethod
    def size(self) -> Size:
        pass

    @size.setter
    @abc.abstractmethod
    def size(self, size: Size):
        pass

    @property
    def rect(self) -> Rect:
        return Rect(self.pos, (self.size.width, self.size.height))


@dataclass
class Size:
    width: int
    height: int


class FixedSize(Size):
    pass


@dataclass
class NaturalSize(Size):
    """A natural size means that the widget itself will choose its size"""
    width: Optional[int] = None
    height: Optional[int] = None


class Button(Widget):
    def __init__(
            self, pos: Optional[Vector2] = None,  size: Size = NaturalSize(),
            child: Optional[Widget] = None, callback: Optional[Callable] = lambda: None):
        self.child = child
        self.callback = callback

        self.padding = 10
        self.border_width = 4
        self.border_color = Color('black')
        self.highlight_color = Color('lightblue')

        # We're setting the size and position at the end because it
        # will call the setter and so it needs the other variables to exist.
        self.pos = pos
        self.size = size

    def draw(self, screen: pygame.Surface):
        super().draw(screen)

        if self.mouse_over:
            pygame.draw.rect(screen, self.highlight_color, self.rect)

        if self.child:
            self.child.draw(screen)

        pygame.draw.rect(screen, self.border_color,
                         self.rect, width=self.border_width)

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.mouse_over:
                self.callback()

    @property
    def mouse_over(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

    @property
    def pos(self) -> Vector2:
        return self._pos

    @pos.setter
    def pos(self, pos: Vector2):
        self._pos = pos
        if self.child:
            padding = Vector2(self.border_width + self.padding)
            self.child.pos = pos + padding

    @property
    def size(self) -> Size:
        if isinstance(self._size, FixedSize):
            return self._size

        elif isinstance(self._size, NaturalSize):
            child_size = self.child.size if self.child else FixedSize(0, 0)
            padding = self.border_width + self.padding
            return NaturalSize(child_size.width + 2 * padding, child_size.height + 2 * padding)

        else:
            raise Exception('Unknown size type')

    @size.setter
    def size(self, size: Size):
        if isinstance(size, FixedSize):
            self._size = size
            if self.child:
                padding = self.border_width + self.padding
                self.child.size = FixedSize(
                    size.width - 2 * padding, size.height - 2 * padding)

        elif isinstance(size, NaturalSize):
            if self.child:
                self.child.size = NaturalSize()
            self._size = NaturalSize()

        else:
            raise Exception('Unknown size type')


class Cursor:
    def __init__(self, index: int = 0, text: Optional[TextRenderer] = None):
        self._index = index
        self._text = text

    @property
    def line(self) -> int:
        for line, (start, end) in enumerate(self._text.line_spans):
            if start <= self.index < end:
                return line

        # If we aren't on any of the lines we must be
        # at the very last position i.e. on the last line.
        return len(self._text.line_spans) - 1

    @line.setter
    def line(self, line: int):
        # TODO: Implement good line setting
        # In most editors when you go up a line, the cursor is placed
        # with an horizontal position that most closely matches the one
        # you had on the previous line. Here, we just place it at the start.
        line = clamp(line, 0, len(self._text.line_spans) - 1)
        start, _ = self._text.line_spans[line]
        self.index = start

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, index: int):
        self._index = clamp(index, 0, len(self._text.text))

    @property
    def window_pos(self) -> Vector2:
        line_start = self._text.line_spans[self.line][0]
        offset_x = sum(advance for (_, _, _, _, advance) in
                       self._text.font.metrics(self._text.text[line_start:self.index]))
        offset_y = self._text.linesize * self.line

        return self._text.pos + Vector2(offset_x, offset_y)

    @window_pos.setter
    def window_pos(self, pos: Vector2):
        x = clamp(pos.x - self._text.pos.x, 0, self._text.width)
        y = clamp(pos.y - self._text.pos.y, 0, self._text.height)

        line = int(y / self._text.linesize)
        line_start, line_end = self._text.line_spans[line]
        line_text = self._text.text[line_start:line_end]

        # Try and find out what character we are at
        offset_x = 0
        for i, (_, _, _, _, advance) in enumerate(self._text.font.metrics(line_text)):
            offset_x += advance
            if x < offset_x:
                span = i
                break
        else:
            # The place the cursor is at isn't on the line so just
            # place the cursor at the end of the line.

            # The last character on the last line is one greater than
            # the length of the text so we need to handle it here.
            if line == len(self._text.line_spans):
                span = len(line_text)
            else:
                span = len(line_text) - 1

        self.index = line_start + span


class Entry(Widget):
    def __init__(
            self, font: pygame.font.Font,  pos: Optional[Vector2] = None,
            size: Size = NaturalSize(), text: str = ''):
        self._text = TextRenderer(Vector2(), text, font)
        self.cursor = Cursor(text=self._text)
        self.focused = False

        self.pos = pos
        self.size = size

    def draw(self, screen: pygame.Surface):
        super().draw(screen)

        self._text.draw(screen)

        if self.focused:
            self._draw_cursor(screen)
            pygame.draw.rect(screen, Color('red'), self.rect, width=4)
        else:
            pygame.draw.rect(screen, Color('black'), self.rect, width=4)

    def _draw_cursor(self, screen):
        cursor_pos = self.cursor.window_pos
        pygame.draw.line(screen, Color('red'),
                         cursor_pos,
                         cursor_pos + Vector2(0, self._text.linesize),
                         width=4)

    def handle(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self.focused = True
                self.cursor.window_pos = Vector2(event.pos)
                pygame.key.start_text_input()
            else:
                self.focused = False
                pygame.key.stop_text_input()

        elif self.focused and event.type == pygame.KEYDOWN:
            # Backspace
            if event.key == pygame.K_BACKSPACE:
                self.remove_span(self.cursor.index - 1)

            # Delete
            elif event.key == pygame.K_DELETE:
                self.remove_span(self.cursor.index)

            # Enter / Return
            elif event.key == pygame.K_RETURN:
                self.insert_str_at(self.cursor.index, '\n')

            # Arrow keys
            elif event.key == pygame.K_RIGHT:
                self.cursor.index += 1
            elif event.key == pygame.K_LEFT:
                self.cursor.index -= 1
            elif event.key == pygame.K_UP:
                self.cursor.line -= 1
            elif event.key == pygame.K_DOWN:
                self.cursor.line += 1

        # Text
        elif self.focused and event.type == pygame.TEXTINPUT:
            self.insert_str_at(self.cursor.index, event.text)

    def remove_span(self, index: int, length: int = 1):
        # If the index is outside the text just return
        if index < 0 or index > len(self._text.text):
            return

        self._text.text = (self._text.text[:index]
                           + self._text.text[index + length:])
        if index < self.cursor.index:
            self.cursor.index -= length

    def insert_str_at(self, index: int, string: str):
        self._text.text = self._text.text[:index] + \
            string + self._text.text[index:]

        # Move the cursor if the string was inserted before it
        if index <= self.cursor.index:
            self.cursor.index += len(string)

    @property
    def text(self) -> str:
        return self._text.text

    @text.setter
    def text(self, text: str):
        self._text.text = text

    @property
    def pos(self) -> Vector2:
        return self._pos

    @pos.setter
    def pos(self, pos: Vector2):
        self._pos = pos
        self._text.pos = pos + Vector2(10)

    @property
    def size(self) -> Size:
        if isinstance(self._size, FixedSize):
            return self._size

        elif isinstance(self._size, NaturalSize):
            return NaturalSize(self._text.width + 20, self._text.height + 20)

        else:
            raise Exception('Unknown size type')

    @size.setter
    def size(self, size: Size):
        if isinstance(size, FixedSize):
            self._size = size
            self._text.max_width = size.width

        elif isinstance(size, NaturalSize):
            self._size = size

        else:
            raise Exception('Unknown size type')


class Text(Widget):
    def __init__(
            self, text: str, font: pygame.font.Font, *,
            pos: Optional[Vector2] = None, size: Size = NaturalSize(),
            color: Color = Color('black')):
        self._text = TextRenderer(Vector2(), text, font, color=color)

        # TODO: Currently the height is ignored.
        # Implementing scroll seems a little insane, so just
        # cutting off the bottom is probably the way to go.
        self.pos = pos
        self.size = size

    def draw(self, screen: pygame.Surface):
        super().draw(screen)

        self._text.draw(screen)

    @property
    def pos(self) -> Vector2:
        return self._pos

    @pos.setter
    def pos(self, pos: Vector2):
        self._pos = pos
        self._text.pos = pos

    @property
    def size(self) -> Size:
        if isinstance(self._size, FixedSize):
            return self._size

        elif isinstance(self._size, NaturalSize):
            return NaturalSize(self._text.width, self._text.height)

        else:
            raise Exception('Unknown size type')

    @size.setter
    def size(self, size: Size):
        if isinstance(size, FixedSize):
            self._size = size
            self._text.max_width = size.width

        elif isinstance(size, NaturalSize):
            self._size = size

        else:
            raise Exception('Unknown size type')

    @property
    def color(self):
        return self._text.color

    @color.setter
    def color(self, color):
        self._text.color = color

    @property
    def text(self):
        return self._text.text

    @text.setter
    def text(self, text):
        self._text.text = text


class TextRenderer:
    def __init__(
            self, pos: Vector2, text: str, font: pygame.font.Font, *,
            color: Color = Color('black'), max_width: Optional[int] = None):
        self.pos = pos
        self._text = text
        self._font = font
        self._color = color
        self._max_width = max_width

        # Dirty means one or more of the properties that
        # are used to render text have changed. It is
        # cleared the next time the text is rendered
        # which is probably when it is draw to the screen.
        self._dirty = True

        self._render()

    def draw(self, surface: pygame.Surface):
        if self._dirty:
            self._render()

        for i, line in enumerate(self._rendered_lines):
            pos = self.pos + Vector2(0, i * self.linesize)
            surface.blit(line, pos)

    @property
    def height(self):
        return self.linesize * len(self._rendered_lines)

    @property
    def width(self):
        return max((line.get_width() for line in self._rendered_lines), default=0)

    @property
    def linesize(self):
        return self._font.get_linesize()

    @property
    def line_spans(self):
        if self._dirty:
            self._render()

        return self._line_spans

    # TODO: I feel there might be a better way to add
    # all these properties, however, my brain is fried.
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._dirty = True

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, font):
        self._font = font
        self._dirty = True

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self._dirty = True

    @property
    def max_width(self):
        return self._max_width

    @max_width.setter
    def max_width(self, max_width):
        self._max_width = max_width
        self._dirty = True

    def _render(self):
        logging.debug('TextUI rendering text')

        self._dirty = False

        # The rendered lines are the lines rendered as
        # surfaces using self._font. The line spans are
        # what spans of the text each line is.
        # So for the line "Hello\nWorld", the line spans
        # would be [(0, 6), (6, 11)] (note '\n' is one char).
        self._rendered_lines = []
        self._line_spans = []

        line_start = 0
        line_end = 0
        i = 0

        # We just keep running until we get an index error
        # i.e. we've hit the end of the string. We aren't quite
        # done there however. There might still be a little bit
        # of string left to render. That is done below in except.
        try:
            while True:
                # Go to the first whitespace character or just move on
                # if we're at the end of the string.
                while i < len(self._text) and not self._text[i].isspace():
                    i += 1

                # We are now at the first whitespace after the current word
                width, _ = self._font.size(self._text[line_start:i])
                if self._max_width is None or width < self._max_width:
                    # If the word fits on the line add it and all the
                    # whitespace that follows it. This assumes that
                    # all whitespace is invisible but that seems like
                    # a reasonable assumption.
                    line_end = i

                    while self._text[i].isspace():
                        # If we meet a newline character we break and start
                        # on a new line. Handled newlines are Linux (\n),
                        # Windows (\r\n) and old Mac (\r).
                        # https://en.wikipedia.org/wiki/Newline#Representation
                        if self._text[i] in ['\n', '\r']:
                            if self._text[i:i+2] == '\r\n':
                                i += 1
                                line_end += 1

                            i += 1
                            line_end += 1

                            # Render the current line and start on a new one
                            self._render_line(line_start, line_end)
                            line_start = line_end
                            break

                        i += 1
                        line_end += 1
                else:
                    # If the word does not fit on the line then render
                    # the current line and start a new line with the
                    # word on it.
                    self._render_line(line_start, line_end)

                    # New line
                    line_start, line_end = line_end, i

        except IndexError:
            # Render all the remaining text
            self._render_line(line_start, len(self._text))

    def _render_line(self, line_start: int, line_end: int):
        line = self._text[line_start:line_end]

        # There might be a newline character(s) at the end of the line.
        # It shows up as a box if it is rendered so we remove it here.
        line = line.strip('\n\r')

        rendered_line = self._font.render(line, True, self._color)
        self._rendered_lines.append(rendered_line)
        self._line_spans.append((line_start, line_end))


def clamp(value, low, high):
    return max(low, min(value, high))
