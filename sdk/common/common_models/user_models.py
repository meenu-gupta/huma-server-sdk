from sdk import convertibleclass

from sdk.common.utils.convertible import default_field


@convertibleclass
class AddressObject:
    FIAT_NUMBER = "fiat_number"
    BUILDING_NUMBER = "building_number"
    BUILDING_NAME = "building_name"
    STREET = "street"
    SUB_STREET = "sub_street"
    TOWN = "town"
    STATE = "state"
    POSTCODE = "postcode"
    COUNTRY = "country"
    LINE1 = "line1"
    LINE2 = "line2"
    LINE3 = "line3"

    fiat_number: str = default_field()
    building_number: str = default_field()
    building_name: str = default_field()
    street: str = default_field()
    sub_street: str = default_field()
    town: str = default_field()
    state: str = default_field()  # https://www.iso.org/obp/ui/#iso:code:3166:US
    postcode: str = default_field()
    country: str = (
        default_field()
    )  # 3 character ISO country code of this address. e.g: GBR
    line1: str = default_field()
    line2: str = default_field()
    line3: str = default_field()
