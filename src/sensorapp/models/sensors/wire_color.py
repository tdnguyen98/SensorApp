"""
    Dataclass for wire color configuration.
    This dataclass is used to represent the configuration of a single wire.
    It contains the wire's label, color and text.

    Label:  The label of the wire. can be "V+", "V-", "RS485A", "RS485B"
    color:  The color of the wire. Can be a single color or a list of 3 colors.
            color="red" for a single color or color=["red", "green", "blue"] for a list of 3 colors or less.
    text:   The text of the wire. Can be a single text or a list of 3 texts.
"""
from dataclasses import dataclass
from typing import List, Union, Optional


@dataclass
class WireColorConfiguration:
    """Represents a single wire's configuration."""

    label: str
    color: Union[str, List[str]]
    text: Optional[Union[str, List[str]]] = None

    def __post_init__(self):
        # Handle color
        if isinstance(self.color, str):
            self.color = [self.color] * 3
        self.color = self.color[:3]
        while len(self.color) < 3:
            self.color.append(self.color[-1])

        # Handle text
        if self.text is None:
            self.text = [""] * 3
        elif isinstance(self.text, str):
            self.text = [self.text] * 3
        self.text = self.text[:3]
        while len(self.text) < 3:
            self.text.append("")
