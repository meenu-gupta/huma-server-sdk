""" Model for Alcohol Consumption object"""
from dataclasses import field
from enum import Enum
from typing import Optional

from extensions.module_result.common.enums import Period
from sdk.common.utils.convertible import convertibleclass, required_field
from .primitive import Primitive


@convertibleclass
class AlcoholItem:
    class AlcoholType(Enum):
        BEER_LAGGER_OR_SIDER = "BEER_LAGGER_OR_SIDER"
        WHINE_OR_SPARKLING_WINE = "WHINE_OR_SPARKLING_WINE"
        SHOTS = "SHOTS"
        ALCOPOPS = "ALCOPOPS"
        FORTIFIED_WINE = "FORTIFIED_WINE"
        SPIRIT = "SPIRIT"
        WINE_OR_SPARKLING_WINE = "WINE_OR_SPARKLING_WINE"
        BEER_LAGER_OR_CIDER = "BEER_LAGER_OR_CIDER"

    class AlcoholAverageStrength(Enum):
        LIGHT = "LIGHT"
        NORMAL = "NORMAL"
        STRONG = "STRONG"

    alcoholType: AlcoholType = required_field()

    # beer and cider and alcopops
    bottleCount: int = field(default=0)
    canCount: int = field(default=0)
    pintCount: int = field(default=0)
    litreCount: int = field(default=0)

    # wine
    largeGlassCount: int = field(default=0)
    standardGlassCount: int = field(default=0)
    smallGlassCount: int = field(default=0)

    # shots
    smallShotCount: int = field(default=0)
    largeShotCount: int = field(default=0)

    # fortified wine
    glassCount: int = field(default=0)

    # spirits
    doubleCount: int = field(default=0)
    largeDoubleCount: int = field(default=0)
    singleCount: int = field(default=0)
    largeSingleCount: int = field(default=0)

    alcoholAverageStrength: AlcoholAverageStrength = required_field()
    period: Period = required_field(default=Period.WEEK)

    def get_consumption_in_ml(self):
        result = (
            self.canCount * 440
            + self.pintCount * 568
            + self.litreCount * 1000
            + self.smallGlassCount * 125
            + self.standardGlassCount * 175
            + self.largeGlassCount * 250
            + self.smallShotCount * 25
            + self.largeShotCount * 35
            + self.glassCount * 50
            + self.singleCount * 25
            + self.largeSingleCount * 35
            + self.doubleCount * 50
            + self.largeDoubleCount * 70
        )

        if (
            self.alcoholType == AlcoholItem.AlcoholType.BEER_LAGGER_OR_SIDER
            or self.alcoholType == AlcoholItem.AlcoholType.BEER_LAGER_OR_CIDER
        ):
            result += self.bottleCount * 330
        if (
            self.alcoholType == AlcoholItem.AlcoholType.WHINE_OR_SPARKLING_WINE
            or self.alcoholType == AlcoholItem.AlcoholType.WINE_OR_SPARKLING_WINE
        ):
            result += self.bottleCount * 750
        if self.alcoholType == AlcoholItem.AlcoholType.ALCOPOPS:
            result += self.bottleCount * 275

        return result

    def get_strength_in_percentage(self):
        strengths = {
            AlcoholItem.AlcoholType.BEER_LAGGER_OR_SIDER.name: {
                AlcoholItem.AlcoholAverageStrength.LIGHT.name: 2,
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 5,
                AlcoholItem.AlcoholAverageStrength.STRONG.name: 7.5,
            },
            AlcoholItem.AlcoholType.BEER_LAGER_OR_CIDER.name: {
                AlcoholItem.AlcoholAverageStrength.LIGHT.name: 2,
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 5,
                AlcoholItem.AlcoholAverageStrength.STRONG.name: 7.5,
            },
            AlcoholItem.AlcoholType.WHINE_OR_SPARKLING_WINE.name: {
                AlcoholItem.AlcoholAverageStrength.LIGHT.name: 11,
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 12.5,
                AlcoholItem.AlcoholAverageStrength.STRONG.name: 14,
            },
            AlcoholItem.AlcoholType.WINE_OR_SPARKLING_WINE.name: {
                AlcoholItem.AlcoholAverageStrength.LIGHT.name: 11,
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 12.5,
                AlcoholItem.AlcoholAverageStrength.STRONG.name: 14,
            },
            AlcoholItem.AlcoholType.SHOTS.name: {
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 40,
            },
            AlcoholItem.AlcoholType.ALCOPOPS.name: {
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 5,
            },
            AlcoholItem.AlcoholType.FORTIFIED_WINE.name: {
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 19,
            },
            AlcoholItem.AlcoholType.SPIRIT.name: {
                AlcoholItem.AlcoholAverageStrength.NORMAL.name: 40,
            },
        }
        return strengths[self.alcoholType.name][self.alcoholAverageStrength.name]

    def get_units(self):
        """
        Note:
        > https://www.nhs.uk/live-well/alcohol-support/calculating-alcohol-units/
        """
        return self.get_strength_in_percentage() * self.get_consumption_in_ml() / 1000.0


@convertibleclass
class AlcoholConsumption(Primitive):
    """Alcohol Consumption model
    NOTE: always per week
    """

    drinkAlcohol: bool = required_field()
    sections: list[AlcoholItem] = required_field()

    def get_estimated_value(self) -> Optional[float]:
        value = 0
        if self.drinkAlcohol:
            total = 0
            for section in self.sections:
                total += section.get_units()
            value = float(total)
        return value
