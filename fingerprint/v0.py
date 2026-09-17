from fingerprint.configurable import ConfigurableDetector
class V0Detector(ConfigurableDetector):
    def __init__(self, signatures: list[dict]) -> None: super().__init__("v0", signatures)
