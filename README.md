# KNX RGB LED – Home Assistant Custom Component

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom component that exposes KNX RGB LEDs using **DPT 232.600** as standard `light` entities.  It supports turning lights on/off, changing color, driving multiple physical KNX group addresses from a single logical light, and persisting the last color across HA restarts.

---

## Features

- 💡 RGB color control (DPT 232.600 – 3-byte telegram)
- 🔌 Sending `0x000000` turns the LED off
- 🔁 Last color is remembered across restarts (no repeated configuration needed)
- 📡 One logical light can write to **multiple** KNX group addresses simultaneously
- 🏠 Multiple independent LED lights supported

---

## Requirements

- Home Assistant **2022.6** or newer
- The built-in [KNX integration](https://www.home-assistant.io/integrations/knx/) must be configured and working

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/twentythree-ch/ha-knx-rgb-led` as category **Integration**.
4. Find **KNX RGB LED** in the HACS store and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/knx_rgb_led` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

Add a `light` platform entry to your `configuration.yaml`:

```yaml
light:
  - platform: knx_rgb_led
    name: "Living Room LED Strip"
    addresses:
      - "1/0/0"

  - platform: knx_rgb_led
    name: "Kitchen Accent LEDs"
    addresses:
      - "1/0/1"
      - "1/0/2"   # both addresses receive the same telegram
```

### Options

| Key | Required | Description |
|-----|----------|-------------|
| `name` | ✅ | Friendly name of the light entity |
| `addresses` | ✅ | List of KNX group addresses (format `M/S/GA`) to write to |

---

## How it works

| Action | KNX telegram |
|--------|-------------|
| Turn **off** | `0x000000` sent to every configured address |
| Turn **on** (no color) | Last used RGB value re-sent |
| Turn **on** with color | New RGB value sent and remembered |

The component accesses the `xknx` instance provided by the built-in KNX integration and sends raw 3-byte `GroupValueWrite` telegrams using **DPT 232.600** encoding.

State (on/off + last color) is restored automatically after a HA restart via `RestoreEntity`.

---

## Troubleshooting

- Make sure the `knx` integration is loaded **before** this component (add it to `configuration.yaml` if not already present).
- Enable debug logging to see sent telegrams:

```yaml
logger:
  logs:
    custom_components.knx_rgb_led: debug
```

---

## Contributing

Pull requests are welcome!  Please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)
