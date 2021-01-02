"""Christmas Lights - Insert Subtitle Here.

Very basic Christmas light patterns on a strip of WS2811 LEDs. This is
guaranteed to be less impressive and more poorly organized than any other
implementation or your money back.
"""

import enum
import time
import typing

from rpi_ws281x import Color, PixelStrip, ws  # type: ignore

# The number of LEDs under control.
_NUM_LEDS = 150


class Colors(enum.Enum):
    """Common colors."""
    NONE = Color(0, 0, 0)
    WARM_WHITE = Color(255, 147, 41)
    CRYSTAL_BLUE = Color(0, 67, 255)
    CRYSTAL_RED = Color(255, 0, 0)
    CRYSTAL_GREEN = Color(0, 255, 0)
    PURE_WHITE = Color(255, 255, 255)


# Some sample colors to stream through, hand-picked by my complete lack of style
# sense.
_DEMO_COLORS = (
    Colors.CRYSTAL_BLUE,
    Colors.CRYSTAL_RED,
    Colors.CRYSTAL_GREEN,
    Colors.PURE_WHITE,
)


def alter_brightness(color: Colors, brightness: float = 1.0) -> int:
    """Modifies the brightness of 'color' by a factor of 'brightness'."""
    return Color(
        int(((color.value >> 16) & 0xFF) * brightness),
        int(((color.value >> 8) & 0xFF) * brightness),
        int((color.value & 0xFF) * brightness),
    )


class LightController:
    """Simple controller for managing a WS2811 RGB LED strip.

    Were you expecting more documentation? Who is reading this anyway?
    """

    def __init__(self, strip: PixelStrip):
        self._strip = strip
        self._strip.begin()

        self._num_pixels = self._strip.numPixels()

    def _set_pixel_color(self, index: int, color: Colors, brightness: float = 1.0):
        """Set the pixel at `index` to `color`."""
        self._strip.setPixelColor(index, alter_brightness(color, brightness))

    def draw_and_erase(self, draw_color: Colors, eraser: Colors, wait_ms=50):
        """Creates a pattern with a 'draw_color' and 'eraser'.

        1. 'draw_color' will be wiped in from the top
        2. 'eraser' will erase the wiped color from the bottom (with a 10-LED
            fading trail)
        """
        for range_idx, pixel_range in enumerate(
                (range(self._num_pixels), range(self._num_pixels, 0, -1))):
            # Range idx 0 -> moving up the strand
            # Range idx 1 -> moving down the strand
            color = draw_color if range_idx else eraser
            for led_idx in pixel_range:
                # Iterate backwards up to 10 pixels, decreasing the color each
                # time and then clearing everything else.
                lower_bound = max(led_idx - 10, 0)
                for bright_idx, i in enumerate(
                        range(led_idx, lower_bound, -1)):
                    brightness = (10 - bright_idx) / 10.0
                    self._set_pixel_color(i, color, brightness)

                # If on the strip, clear out the 11th pixel.
                if lower_bound > 0:
                    self._set_pixel_color(lower_bound, Colors.NONE)

                self._show_with_delay(wait_ms)

    def christmas_colors(self, wait_ms=50):
        """Standard, static Christmas colors."""
        for i in range(0, self._num_pixels, 3):
            self._set_pixel_color(i, Colors.PURE_WHITE, brightness=0.4)
            self._set_pixel_color(i + 1, Colors.CRYSTAL_RED, brightness=0.4)
            self._set_pixel_color(i + 2, Colors.CRYSTAL_GREEN, brightness=0.4)

        self._show_with_delay(wait_ms)

        self._show_with_delay(wait_ms)

    def pulse(self, color: Colors, wait_ms=50):
        """Pulses color by reducing and then increasing brightness."""
        for brightness in range(1, 10):
            for i in range(self._num_pixels):
                self._set_pixel_color(i, color, brightness=brightness / 10)

            self._show_with_delay(wait_ms)

        # And back down.
        for brightness in range(10, 1, -1):
            for i in range(self._num_pixels):
                self._set_pixel_color(i, color, brightness=brightness / 10)

            self._show_with_delay(wait_ms)

    def pulse_between(self, colors: typing.Sequence[Colors], wait_ms=50):
        """Helper for pulsing between multiple colors."""
        for color in colors:
            self.pulse(color, wait_ms)

    def candy_cane(self, wait_ms=50):
        """Sets a base white and then sends a fading red chaser through it."""
        # Base.
        for i in range(self._num_pixels):
            self._set_pixel_color(i, Colors.PURE_WHITE)

        self._show_with_delay(wait_ms)

        # Chaser.
        self.vapor_trail(
            color=Colors.CRYSTAL_RED,
            trail_color=Colors.PURE_WHITE,
            wait_ms=wait_ms)

    def vapor_trail(
            self, color: Colors, trail=10, trail_color: Colors = Colors.NONE, wait_ms=50):
        """Creates a pattern where 'color' moves along the strand.

        'trail' is the number of pixels in the trail behind 'color', which will
        be increasingly dimmed the further they are from the front.

        'trail_color' is the color to which pixels *after* the trail will be set
        (i.e. if the strand already has a color this can be used to 'reset' the
        color after the vapor trail has finished).
        """
        # Note that the first pass of this lights up the first 10 pixels.
        # Although that this appallingly sloppy, it also won't be noticeable
        # after the first time the path loops back to the beginning so just keep
        # it simple.

        for led_idx in range(self._num_pixels):
            # Iterate through the next 'trail' pixels, incrementing the
            # brightness to reach the target color. If the index 'falls' off the
            # end (e.g. the index is less than 'trail' pixels from the end),
            # don't update further - this allows the effect to fully fade off
            # the strand.

            # Note: when this runs off the end of the strand it will loop back
            # to the first pixel, what fun.
            upper_bound = led_idx + trail
            for offset, trail_idx in enumerate(range(led_idx, upper_bound)):
                # Work up towards the target.
                brightness = offset / float(trail)
                self._set_pixel_color(
                    (led_idx + offset) % self._num_pixels, color, brightness)

            # If on the strip, clear out the 11th pixel.
            if led_idx >= 0:
                self._set_pixel_color(led_idx, trail_color)

            self._show_with_delay(wait_ms)

    def alternating_colors(self, first: Colors, second: Colors, wait_ms=50):
        for i in range(0, self._num_pixels, 2):
            self._set_pixel_color(i, first)
            self._set_pixel_color(i + 1, second)

        self._show_with_delay(wait_ms)

    def single_color(self, color: Colors, wait_ms=50):
        """Apply a single color to all pixels."""
        for i in range(self._num_pixels):
            self._set_pixel_color(i, color)

        self._show_with_delay(wait_ms)

    def _show_with_delay(self, wait_ms=50):
        """Show the current strip state and hold it for `wait_ms`."""
        self._strip.show()
        time.sleep(wait_ms / 1000.0)

    def Run(self):
        while True:
            # Solid color.
            self.single_color(Colors.CRYSTAL_BLUE, wait_ms=50)

            # Alternating colors.
            self.alternating_colors(
                first=Colors.CRYSTAL_BLUE,
                second=Colors.PURE_WHITE,
                wait_ms=50)

            # Transitions between colors.
            self.pulse_between(
                (Colors.WARM_WHITE, Colors.CRYSTAL_BLUE), wait_ms=50)
            for color in _DEMO_COLORS:
                self.pulse(color, wait_ms=75)

            # Christmas-y stuff.
            self.christmas_colors()
            self.candy_cane()

            # Draw a color then erase it.
            for color in _DEMO_COLORS:
                self.draw_and_erase(draw_color=color, eraser=Colors.WARM_WHITE)

            # Fading streamers.
            for color in _DEMO_COLORS:
                self.vapor_trail(color=color, trail=20)


if __name__ == "__main__":
    # Initialize. At some point these could be made flags/etc., maybe next
    # Christmas...
    print("Running...")
    strip = PixelStrip(num=_NUM_LEDS, pin=18, strip_type=ws.WS2811_STRIP_RGB)

    controller = LightController(strip)
    controller.Run()
