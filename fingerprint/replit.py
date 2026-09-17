from fingerprint.configurable import ConfigurableDetector
class ReplitDetector(ConfigurableDetector):
    def __init__(self, signatures: list[dict]) -> None: super().__init__("replit", signatures)
