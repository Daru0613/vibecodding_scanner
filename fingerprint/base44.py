from fingerprint.configurable import ConfigurableDetector
class Base44Detector(ConfigurableDetector):
    def __init__(self, signatures: list[dict]) -> None: super().__init__("base44", signatures)
