from typing import Dict, Any
from ...enums import ConfigKey, TERM


DEFAULT_SETTINGS: Dict[ConfigKey, Any] = {
    ConfigKey.SHOW_TERMINAL: False,
    ConfigKey.TERMINAL_SIZE: TERM.MEDIUM,
    ConfigKey.CARD_TRANSPARENCY: 72,
}
