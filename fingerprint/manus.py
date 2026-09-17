from fingerprint.configurable import ConfigurableDetector
class ManusDetector(ConfigurableDetector):
    def __init__(self, signatures: list[dict]) -> None: super().__init__("manus", signatures)
