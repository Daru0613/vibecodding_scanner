from fingerprint.configurable import ConfigurableDetector


class LovableDetector(ConfigurableDetector):
    def __init__(self, signatures: list[dict]) -> None: super().__init__("lovable", signatures)

