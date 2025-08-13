import re
import hashlib
from typing import Optional


def _to_snake(text: str) -> str:
	"""Normalize to a simple snake_case identifier."""
	# Remove bracket wrappers if present
	t = text.strip()
	if t.startswith('[') and t.endswith(']'):
		t = t[1:-1]
	# Lower and remove obvious year tokens
	t = re.sub(r"\b(19|20)\d{2}\b", "", t.lower())
	# Replace non-alphanum with spaces then collapse
	t = ''.join(ch if ch.isalnum() else ' ' for ch in t)
	t = re.sub(r"\s+", " ", t).strip()
	return t.replace(' ', '_')


def canonicalize_variable_name(raw_name: str, var_type: Optional[str] = None) -> str:
	"""Derive a stable canonical key for a placeholder name using keywords.

	This is intentionally heuristic but stable across year phrasing changes.
	"""
	name = raw_name or ""
	base = name.lower()
	# Fast paths by keywords
	if 'plan name' in base:
		return 'plan_name'
	if 'mao name' in base or 'organization' in base:
		return 'organization_name'
	if 'customer service' in base and ('phone' in base or 'number' in base):
		return 'customer_service_phone'
	if 'phone number' in base or ('phone' in base and 'tty' not in base):
		return 'phone_number'
	if 'tty' in base:
		return 'tty_number'
	if 'hours of operation' in base or ('hours' in base and 'operation' in base):
		return 'hours_of_operation'
	if 'provider directory' in base and ('url' in base or 'website' in base or 'direct url' in base):
		return 'provider_directory_url'
	if 'url' in base or 'website' in base:
		return 'url'
	if 'premium' in base and ('amount' in base or 'monthly' in base):
		return 'premium_amount'
	# Type-based fallback
	if var_type:
		vt = var_type.lower()
		if vt in {
			'plan_name','organization','phone_number','tty_number','business_hours','url','financial','date_time','address'
		}:
			return vt
	# Generic normalized token fallback
	return _to_snake(base)


def _normalize_for_signature(text: str) -> str:
	# Lower, remove years, collapse whitespace and punctuation
	t = text or ''
	t = re.sub(r"\b(19|20)\d{2}\b", "", t.lower())
	t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
	t = re.sub(r"\s+", " ", t).strip()
	return t


def _hash(text: str) -> str:
	return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def build_context_signatures(before_context: str, after_context: str) -> dict:
	"""Create short hashes of before/after text for alignment hints."""
	bn = _normalize_for_signature(before_context or '')
	an = _normalize_for_signature(after_context or '')
	return {
		'before_sig': _hash(bn),
		'after_sig': _hash(an)
	}


