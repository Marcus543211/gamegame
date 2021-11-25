import logging
from typing import Optional

import pygame
from pygame import Color, Vector2


class TextRenderer:
    def __init__(
            self, position: Vector2, text: str, font: pygame.font.Font, *,
            color: Color = Color('black'), max_width: Optional[int] = None):
        self.position = position
        self._text = text
        self._font = font
        self._color = color
        self._max_width = max_width

        self._render()

    def draw(self, surface):
        line_space = self._font.get_linesize()
        for i, line in enumerate(self._rendered):
            position = self.position + Vector2(0, i * line_space)
            surface.blit(line, position)

    # TODO: I feel there might be a better way to add
    # all these properties, however, my brain is fried.
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._render()

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, font):
        self._font = font
        self._render()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self._render()

    @property
    def max_width(self):
        return self._max_width

    @max_width.setter
    def max_width(self, max_width):
        self._max_width = max_width
        self._render()

    def _render(self):
        logging.debug('TextUI rendering text')

        self._rendered = []

        if self._max_width is None:
            self._render_text(self._text)
            return

        # Split the text up at newlines and then render
        # each of the given paragraphs individually.
        # I call them paragraphs because "line" is a bit
        # confusing when the splits are also called lines.
        for paragraph in self._text.splitlines():
            self._render_paragraph(paragraph)

    def _render_paragraph(self, paragraph: text):
        line_start = 0
        line_end = 0
        # The current word starts where the current lines end
        current_word_end = 0
        i = 0

        # We just keep running until we get an index error
        # i.e. we've hit the end of the string. We aren't quite
        # done there however. There might still be a little bit
        # of string left to render. That is done below in except.
        try:
            while True:
                # Go to the first whitespace character or just move on
                # if we're at the end of the string.
                while i < len(paragraph) and not paragraph[i].isspace():
                    i += 1
                    current_word_end += 1

                # We are now at the first whitespace after the current word
                width, _height = self._font.size(
                    paragraph[line_start:current_word_end])
                if width < self._max_width:
                    # If the word fits on the line add it and all the
                    # whitespace that follows it. This assumes that
                    # all whitespace is invisible but that seems like
                    # a reasonable assumption.
                    while paragraph[i].isspace():
                        i += 1
                        current_word_end += 1
                    line_end = current_word_end
                else:
                    # If the word does not fit on the line then render
                    # the current line and start a new line with the
                    # word on it.
                    self._render_text(paragraph[line_start:line_end])

                    # New line
                    line_start, line_end = line_end, current_word_end

        except IndexError:
            self._render_text(paragraph[line_start:current_word_end])

    def _render_text(self, line: str):
        self._rendered.append(self._font.render(line, True, self._color))
