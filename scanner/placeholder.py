"""Extension point for future consented security/privacy scanners.

This release intentionally performs no vulnerability probing and stores no personal data.
Future findings should retain only finding_type, masked_value, value_hash, source_url,
and location—never raw sensitive values.
"""

