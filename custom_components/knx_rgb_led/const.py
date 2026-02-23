"""Constants for KNX RGB LED."""

DOMAIN = "knx_rgb_led"
CONF_ADDRESSES = "addresses"
DEFAULT_COLOR: tuple[int, int, int] = (255, 255, 255)

# Light effect names
EFFECT_BLINK_SLOW = "Blink Slow"
EFFECT_BLINK_MEDIUM = "Blink Medium"
EFFECT_BLINK_RAPID = "Blink Rapid"

# Blink intervals: (on_seconds, off_seconds)
BLINK_INTERVALS: dict[str, tuple[float, float]] = {
    EFFECT_BLINK_SLOW: (2.0, 2.0),
    EFFECT_BLINK_MEDIUM: (0.75, 0.75),
    EFFECT_BLINK_RAPID: (0.25, 0.25),
}
