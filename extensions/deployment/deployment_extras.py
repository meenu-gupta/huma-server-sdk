"""model for deployment extras"""
from dataclasses import field

from sdk.common.utils.convertible import convertibleclass, meta


@convertibleclass
class DeploymentExtras:
    HAS_DEVICE_INTEGRATION = "hasDeviceIntegration"
    HAS_CLINICIAN_SEEN_INDICATOR = "hasClinicianSeenIndicator"

    hasDeviceIntegration: bool = field(default=False, metadata=meta(required=False))
    hasClinicianSeenIndicator: bool = field(
        default=False, metadata=meta(required=False)
    )
