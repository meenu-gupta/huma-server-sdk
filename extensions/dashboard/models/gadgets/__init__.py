from .base_gadget import Gadget
from .consented import ConsentedGadget
from .key_metrics import KeyMetricsGadget
from .overall_view import OverallViewGadget
from .signed_up import SignedUpGadget

existing_gadgets = (
    ConsentedGadget,
    SignedUpGadget,
    KeyMetricsGadget,
    OverallViewGadget,
)
