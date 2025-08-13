#!/usr/bin/env python3
"""
Simple, reliable mapping system rebuilt from the ground up.
Focuses on core functionality: find variables, extract values using context.
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from docx import Document
from logging_config import logger


class SimpleMapper:
    """Simple, reliable variable mapper using context-based extraction."""
    
    def __init__(self):
        self.extracted_values = {}
        self.extraction_log = []
    
    def map_documents(self, model_docx_path: str, final_docx_path: str, 
                     progress_callback=None, log_callback=None) -> Tuple[Dict[str, str], List[Dict]]:
        """
        Main mapping function - simple and reliable.
        
        Args:
            model_docx_path: Path to model document with [variables]
            final_docx_path: Path to final document with actual values
            progress_callback: Function to report progress
            log_callback: Function to log messages
            
        Returns:
            Tuple of (extracted_values, extraction_logs)
        """
        try:
            if log_callback:
                log_callback("🚀 Starting simple document mapping...")
            
            # Step 1: Extract all variables from model document
            model_variables = self._extract_variables_from_model(model_docx_path)
            total_vars = len(model_variables)
            
            if log_callback:
                log_callback(f"📋 Found {total_vars} variables in model document")
            
            if total_vars == 0:
                if log_callback:
                    log_callback("⚠️ No variables found in model document")
                return {}, []
            
            # Step 2: Read final document content
            final_content = self._read_document_content(final_docx_path)
            
            if log_callback:
                log_callback(f"📄 Loaded final document ({len(final_content)} characters)")
            
            # Step 3: Extract values for each variable
            for i, var_info in enumerate(model_variables):
                if progress_callback:
                    progress = ((i + 1) / total_vars) * 100
                    progress_callback(progress)
                
                var_name = var_info['variable']
                context_before = var_info['before_context']
                context_after = var_info['after_context']
                
                if log_callback:
                    log_callback(f"🔍 [{i+1}/{total_vars}] Processing: {var_name}")
                
                # Extract the value
                extracted_value, confidence, method = self._extract_value(
                    var_name, context_before, context_after, final_content
                )
                
                # Store result
                self.extracted_values[var_name] = extracted_value
                
                # Log the extraction
                log_entry = {
                    'variable': var_name,
                    'extracted_value': extracted_value,
                    'confidence': confidence,
                    'method': method,
                    'before_context': context_before[:50],
                    'after_context': context_after[:50]
                }
                self.extraction_log.append(log_entry)
                
                if log_callback:
                    status = "✅" if extracted_value != "None" else "⚠️"
                    log_callback(f"   {status} Result: '{extracted_value}' ({method}, {confidence:.0%})")
            
            # Final summary
            successful = sum(1 for v in self.extracted_values.values() if v != "None")
            success_rate = (successful / total_vars) * 100 if total_vars > 0 else 0
            
            if log_callback:
                log_callback(f"📊 Extraction complete: {successful}/{total_vars} variables ({success_rate:.0f}%)")
            
            return self.extracted_values, self.extraction_log
            
        except Exception as e:
            error_msg = f"Error in simple mapping: {e}"
            logger.error(error_msg)
            if log_callback:
                log_callback(f"❌ {error_msg}")
            return {}, []
    
    def _extract_variables_from_model(self, model_docx_path: str) -> List[Dict]:
        """Extract all variables and their context from model document."""
        variables = []
        
        try:
            doc = Document(model_docx_path)
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text or '[' not in text:
                    continue
                
                # Find all variables in this paragraph
                variable_matches = list(re.finditer(r'\[([^\]]+)\]', text))
                
                for match in variable_matches:
                    var_name = match.group(1).strip()
                    var_start, var_end = match.span()
                    
                    # Extract context before and after the variable
                    before_context = text[:var_start].strip()
                    after_context = text[var_end:].strip()
                    
                    # Take last 3-5 words before, first 3-5 words after
                    before_words = before_context.split()[-5:] if before_context else []
                    after_words = after_context.split()[:5] if after_context else []
                    
                    before_context = " ".join(before_words)
                    after_context = " ".join(after_words)
                    
                    variables.append({
                        'variable': var_name,
                        'before_context': before_context,
                        'after_context': after_context,
                        'full_text': text
                    })
            
            return variables
            
        except Exception as e:
            logger.error(f"Error extracting variables from model: {e}")
            return []
    
    def _read_document_content(self, docx_path: str) -> str:
        """Read all content from a DOCX document."""
        try:
            doc = Document(docx_path)
            content_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    content_parts.append(para.text.strip())
            
            return " ".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error reading document content: {e}")
            return ""
    
    def _extract_value(self, variable_name: str, before_context: str, after_context: str, 
                      final_content: str) -> Tuple[str, float, str]:
        """
        Extract value for a variable using multiple strategies.
        
        Returns:
            Tuple of (extracted_value, confidence, method)
        """
        # Strategy 1: Use before context to find the value
        if before_context and len(before_context.split()) >= 2:
            value, confidence = self._extract_using_before_context(
                variable_name, before_context, after_context, final_content
            )
            if confidence > 0.7:
                return value, confidence, "before_context"
        
        # Strategy 2: Use after context to find the value
        if after_context and len(after_context.split()) >= 2:
            value, confidence = self._extract_using_after_context(
                variable_name, before_context, after_context, final_content
            )
            if confidence > 0.7:
                return value, confidence, "after_context"
        
        # Strategy 3: Use both contexts for precise extraction
        if before_context and after_context:
            value, confidence = self._extract_using_both_contexts(
                variable_name, before_context, after_context, final_content
            )
            if confidence > 0.5:
                return value, confidence, "both_contexts"
        
        # Strategy 4: Smart patterns for known variable types
        value, confidence = self._extract_using_smart_patterns(
            variable_name, final_content
        )
        if confidence > 0.5:
            return value, confidence, "smart_pattern"
        
        # Strategy 5: Enhanced pattern matching with fuzzy context
        value, confidence = self._extract_using_enhanced_patterns(
            variable_name, before_context, after_context, final_content
        )
        if confidence > 0.4:
            return value, confidence, "enhanced_pattern"
        
        return "None", 0.0, "no_match"
    
    def _extract_using_before_context(self, variable_name: str, before_context: str, 
                                    after_context: str, final_content: str) -> Tuple[str, float]:
        """Extract value by finding the before context and taking what comes after."""
        try:
            # Look for the before context in the final document
            before_lower = before_context.lower()
            content_lower = final_content.lower()
            
            # Find the position of before context
            context_pos = content_lower.find(before_lower)
            if context_pos >= 0:
                # Found the context! Extract what comes after it
                start_pos = context_pos + len(before_lower)
                remaining_text = final_content[start_pos:].strip()
                
                # Extract the value based on variable type
                extracted_value = self._extract_value_by_type(variable_name, remaining_text, after_context)
                
                if extracted_value and extracted_value != "None":
                    return extracted_value, 0.9
            
            return "None", 0.0
            
        except Exception as e:
            logger.error(f"Error in before context extraction: {e}")
            return "None", 0.0
    
    def _extract_using_after_context(self, variable_name: str, before_context: str,
                                   after_context: str, final_content: str) -> Tuple[str, float]:
        """Extract value by finding the after context and taking what comes before."""
        try:
            after_lower = after_context.lower()
            content_lower = final_content.lower()
            
            # Find the position of after context
            context_pos = content_lower.find(after_lower)
            if context_pos >= 0:
                # Found the context! Extract what comes before it
                preceding_text = final_content[:context_pos].strip()
                
                # Take the last few meaningful words/phrases
                words = preceding_text.split()
                if len(words) >= 3:
                    # For plan names, take more words; for others, take fewer
                    if 'plan name' in variable_name.lower():
                        extracted_value = " ".join(words[-4:])  # Last 4 words
                    else:
                        extracted_value = " ".join(words[-2:])  # Last 2 words
                    
                    return extracted_value, 0.8
            
            return "None", 0.0
            
        except Exception as e:
            logger.error(f"Error in after context extraction: {e}")
            return "None", 0.0
    
    def _extract_using_both_contexts(self, variable_name: str, before_context: str,
                                   after_context: str, final_content: str) -> Tuple[str, float]:
        """Extract value by finding both contexts and taking what's between them."""
        try:
            before_lower = before_context.lower()
            after_lower = after_context.lower()
            content_lower = final_content.lower()
            
            # Find both contexts
            before_pos = content_lower.find(before_lower)
            after_pos = content_lower.find(after_lower)
            
            if before_pos >= 0 and after_pos >= 0 and after_pos > before_pos:
                # Found both! Extract what's between them
                start_pos = before_pos + len(before_lower)
                between_text = final_content[start_pos:after_pos].strip()
                
                # Clean up the extracted text
                between_text = re.sub(r'^[^\w]+|[^\w]+$', '', between_text)
                
                if between_text:
                    return between_text, 0.95  # Very high confidence
            
            return "None", 0.0
            
        except Exception as e:
            logger.error(f"Error in both contexts extraction: {e}")
            return "None", 0.0
    
    def _extract_using_smart_patterns(self, variable_name: str, final_content: str) -> Tuple[str, float]:
        """Extract value using smart patterns for known variable types."""
        var_lower = variable_name.lower()
        
        try:
            # TTY numbers are almost always 711
            if 'tty' in var_lower:
                if '711' in final_content:
                    return "711", 0.99
            
            # Phone numbers (including Customer Services numbers)
            if ('phone' in var_lower or 'customer service' in var_lower or 
                'customer services' in var_lower or 'contact' in var_lower):
                phone_pattern = r'(\d{1}-\d{3}-\d{3}-\d{4})'
                match = re.search(phone_pattern, final_content)
                if match:
                    return match.group(1), 0.95
            
            # URL extraction  
            if 'url' in var_lower or 'website' in var_lower:
                url_patterns = [
                    r'https?://([^\s]+)',  # Full URLs with protocol
                    r'www\.([^\s]+)',      # www URLs
                    r'([a-zA-Z0-9.-]+\.com[^\s]*)',  # .com domains
                    r'([a-zA-Z0-9.-]+\.org[^\s]*)',  # .org domains
                    r'([a-zA-Z0-9.-]+\.gov[^\s]*)'   # .gov domains
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, final_content, re.IGNORECASE)
                    if matches:
                        url = matches[0].rstrip('.,;)')
                        if not url.startswith('http'):
                            url = f"https://{url}" if url.startswith('www.') else f"https://www.{url}"
                        return url, 0.95
            
            # Plan names (look for patterns like "Medicare Plus Blue Group PPO")
            elif 'plan name' in var_lower:
                plan_patterns = [
                    r'(Medicare\s+Plus\s+Blue\s+Group\s+PPO)',
                    r'(Medicare\s+Plus\s+Blue\s+PPO)',
                    r'([A-Z][a-z]+\s+Plus\s+[A-Z][a-z]+\s+Group\s+PPO)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+PPO)'
                ]
                
                for pattern in plan_patterns:
                    match = re.search(pattern, final_content, re.IGNORECASE)
                    if match:
                        return match.group(1), 0.8
            
            # Organization names (like "Blue Cross Blue Shield of Michigan")
            if 'mao name' in var_lower or 'organization' in var_lower:
                org_patterns = [
                    r'(Blue\s+Cross\s+Blue\s+Shield\s+of\s+[A-Z][a-z]+)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+of\s+[A-Z][a-z]+)'
                ]
                
                for pattern in org_patterns:
                    match = re.search(pattern, final_content, re.IGNORECASE)
                    if match:
                        return match.group(1), 0.8
            
            return "None", 0.0
            
        except Exception as e:
            logger.error(f"Error in smart pattern extraction: {e}")
            return "None", 0.0
    
    def _extract_using_enhanced_patterns(self, variable_name: str, before_context: str,
                                       after_context: str, final_content: str) -> Tuple[str, float]:
        """Enhanced pattern matching without AI dependency."""
        try:
            var_lower = variable_name.lower()
            content_lower = final_content.lower()
            
            # Enhanced TTY extraction
            if 'tty' in var_lower:
                # Look for TTY patterns
                tty_patterns = [
                    r'tty\s*(\d+)',
                    r'tty\s+(\d+)',
                    r'tty:\s*(\d+)',
                    r'\(tty\s+(\d+)\)',
                    r'tty\s+users?\s+call\s+(\d+)'
                ]
                
                for pattern in tty_patterns:
                    match = re.search(pattern, content_lower)
                    if match:
                        return match.group(1), 0.9
                
                # Default TTY fallback
                if '711' in final_content:
                    return "711", 0.8
            
            # Enhanced plan name extraction
            elif 'plan name' in var_lower:
                # Look for plan name patterns with surrounding context
                plan_patterns = [
                    r'plan,?\s+([A-Z][a-z]+(?:\s+[A-Z&+][a-z]*)*(?:\s+(?:PPO|HMO|Group|Plus|Blue))*)',
                    r'member\s+of\s+([A-Z][a-z]+(?:\s+[A-Z&+][a-z]*)*(?:\s+(?:PPO|HMO|Group|Plus|Blue))*)',
                    r'coverage\s+through\s+([A-Z][a-z]+(?:\s+[A-Z&+][a-z]*)*(?:\s+(?:PPO|HMO|Group|Plus|Blue))*)',
                    r'([A-Z][a-z]+\s+Plus\s+Blue\s+(?:Group\s+)?PPO)',
                    r'(Medicare\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:PPO|HMO|Group))*)'
                ]
                
                for pattern in plan_patterns:
                    match = re.search(pattern, final_content)
                    if match:
                        plan_name = match.group(1).strip()
                        # Clean up the plan name
                        plan_name = re.sub(r'^(the|a|an)\s+', '', plan_name, flags=re.IGNORECASE)
                        if len(plan_name.split()) >= 2:  # Ensure it's not just one word
                            return plan_name, 0.85
            
            # Enhanced organization/MAO name extraction
            elif 'mao name' in var_lower or 'organization' in var_lower:
                org_patterns = [
                    r'offered\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s+of\s+[A-Z][a-z]+)*)',
                    r'provided\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                    r'(Blue\s+Cross\s+Blue\s+Shield\s+of\s+[A-Z][a-z]+)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Insurance|Health|Medical|Corporation))',
                    r'contact\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
                ]
                
                for pattern in org_patterns:
                    match = re.search(pattern, final_content)
                    if match:
                        org_name = match.group(1).strip()
                        if len(org_name.split()) >= 2:
                            return org_name, 0.8
            
            # Enhanced phone number extraction (including Customer Services numbers)
            elif ('phone' in var_lower or 'customer service' in var_lower or 
                  'customer services' in var_lower or 'contact' in var_lower):
                phone_patterns = [
                    r'call\s+([1-]?\d{3}[-.]?\d{3}[-.]?\d{4})',
                    r'phone:?\s+([1-]?\d{3}[-.]?\d{3}[-.]?\d{4})',
                    r'(\d{1}-\d{3}-\d{3}-\d{4})',
                    r'(\(\d{3}\)\s*\d{3}[-.]?\d{4})',
                    r'(\d{3}[-.]?\d{3}[-.]?\d{4})'
                ]
                
                for pattern in phone_patterns:
                    match = re.search(pattern, final_content)
                    if match:
                        phone = match.group(1)
                        # Format the phone number consistently
                        digits = re.sub(r'[^\d]', '', phone)
                        if len(digits) == 10:
                            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}", 0.9
                        elif len(digits) == 11 and digits.startswith('1'):
                            return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}", 0.9
                        else:
                            return phone, 0.7
            
            # Enhanced hours of operation extraction
            elif ('hours' in var_lower and 'operation' in var_lower) or ('days' in var_lower and 'hours' in var_lower):
                hours_patterns = [
                    r'([A-Z][a-z]+\s+through\s+[A-Z][a-z]+,?\s+\d+\s*[ap]\.?m\.?\s+to\s+\d+\s*[ap]\.?m\.?)',
                    r'([A-Z][a-z]+\s*-\s*[A-Z][a-z]+,?\s+\d+:\d+\s*[AP]M\s+to\s+\d+:\d+\s*[AP]M)',
                    r'([A-Z][a-z]+\s+to\s+[A-Z][a-z]+\s+from\s+\d+\s*[ap]\.?m\.?\s+to\s+\d+\s*[ap]\.?m\.?)',
                    r'(\d+\s*[ap]\.?m\.?\s+to\s+\d+\s*[ap]\.?m\.?,?\s+[A-Z][a-z]+\s+through\s+[A-Z][a-z]+)',
                    r'(\d+\s*[ap]\.?m\.?\s*-\s*\d+\s*[ap]\.?m\.?,?\s+[A-Z][a-z]+\s*-\s*[A-Z][a-z]+)'
                ]
                
                for pattern in hours_patterns:
                    match = re.search(pattern, final_content, re.IGNORECASE)
                    if match:
                        return match.group(1), 0.8
            
            # Enhanced URL extraction
            elif 'url' in var_lower or 'website' in var_lower:
                url_patterns = [
                r'https?://([^\s]+)',  # Full URLs with protocol
                r'www\.([^\s]+)',      # www URLs
                r'([a-zA-Z0-9.-]+\.com[^\s]*)',  # .com domains
                r'([a-zA-Z0-9.-]+\.org[^\s]*)',  # .org domains
                r'([a-zA-Z0-9.-]+\.gov[^\s]*)',  # .gov domains
                r'([a-zA-Z0-9.-]+\.edu[^\s]*)'   # .edu domains
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, final_content, re.IGNORECASE)
                    if matches:
                        url = matches[0]
                        # Clean up the URL and ensure proper format
                        url = url.rstrip('.,;)')  # Remove trailing punctuation
                        
                        # Add protocol if missing
                        if not re.match(r'^https?://', url):
                            if url.startswith('www.'):
                                url = f"https://{url}"
                            else:
                                url = f"https://www.{url}" if not url.startswith('www.') else f"https://{url}"
                        
                        return url, 0.9
                    
            # Enhanced template content extraction (for "Insert if applicable" with template content)
            elif 'insert if applicable' in var_lower or self._has_template_content(variable_name):
                return self._extract_template_content(variable_name, final_content)
            
            # Enhanced multi-option selection extraction
            elif ('select one' in var_lower or 'or' in var_lower) and ('copayment' in var_lower or 'coinsurance' in var_lower):
                # This is a multi-option scenario - extract which option was actually selected
                return self._extract_multi_option_selection(variable_name, before_context, after_context, final_content)
            
            # Enhanced state/location extraction
            elif 'state' in var_lower:
                # Look for state names in context
                states = [
                    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
                    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
                    'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
                    'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
                    'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
                    'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
                    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
                    'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
                    'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
                    'West Virginia', 'Wisconsin', 'Wyoming'
                ]
                
                for state in states:
                    if state.lower() in content_lower:
                        return state, 0.9
            
            # Try fuzzy context matching if we have context
            if before_context:
                value, confidence = self._fuzzy_context_extraction(
                    before_context, after_context, final_content
                )
                if confidence > 0.4:
                    return value, confidence
            
            return "None", 0.0
            
        except Exception as e:
            logger.error(f"Error in enhanced pattern extraction: {e}")
            return "None", 0.0
    
    def _fuzzy_context_extraction(self, before_context: str, after_context: str, 
                                final_content: str) -> Tuple[str, float]:
        """Fuzzy matching for context when exact matches fail."""
        try:
            # Split context into words for fuzzy matching
            before_words = before_context.lower().split() if before_context else []
            after_words = after_context.lower().split() if after_context else []
            
            if not before_words:
                return "None", 0.0
            
            # Look for partial word matches in the content
            content_words = final_content.lower().split()
            
            # Find the best matching position for before context
            best_position = -1
            best_score = 0
            
            for i in range(len(content_words) - len(before_words) + 1):
                # Calculate match score for this position
                score = 0
                for j, word in enumerate(before_words):
                    if i + j < len(content_words) and word in content_words[i + j]:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_position = i
            
            # If we found a reasonable match, extract what comes after
            if best_position >= 0 and best_score >= len(before_words) * 0.5:
                start_pos = best_position + len(before_words)
                
                # Extract the next 1-4 words as the value
                if start_pos < len(content_words):
                    # Determine how many words to take
                    num_words = min(4, len(content_words) - start_pos)
                    
                    # If we have after context, limit by that
                    if after_words:
                        for k in range(num_words):
                            if start_pos + k < len(content_words):
                                word = content_words[start_pos + k]
                                if any(after_word in word for after_word in after_words[:2]):
                                    num_words = k
                                    break
                    
                    if num_words > 0:
                        extracted_words = content_words[start_pos:start_pos + num_words]
                        # Reconstruct with proper capitalization from original text
                        value = " ".join(extracted_words)
                        confidence = (best_score / len(before_words)) * 0.7  # Max 0.7 for fuzzy
                        return value, confidence
            
            return "None", 0.0
            
        except Exception as e:
            logger.error(f"Error in fuzzy context extraction: {e}")
            return "None", 0.0
    
    def _extract_value_by_type(self, variable_name: str, text: str, after_context: str) -> str:
        """Extract value from text based on the variable type."""
        var_lower = variable_name.lower()
        
        # For plan names, look for capitalized sequences
        if 'plan name' in var_lower:
            # Look for capitalized words, possibly ending with PPO/HMO/Group
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:PPO|HMO|Group|Plus|Blue))*)'
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                # Stop at after context if present
                if after_context:
                    for word in after_context.split()[:2]:
                        if word.lower() in value.lower():
                            value = value.split(word)[0].strip()
                            break
                return value
        
        # For organization names, look for multiple capitalized words
        if 'mao name' in var_lower or 'organization' in var_lower:
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s+of\s+[A-Z][a-z]+)*)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # General extraction: take the next meaningful phrase
        pattern = r'([^.!?;,\[\]]+)'
        match = re.match(pattern, text)
        if match:
            value = match.group(1).strip()
            
            # Stop at after context
            if after_context:
                for word in after_context.split()[:2]:
                    if word.lower() in value.lower():
                        value = value.split(word)[0].strip()
                        break
            
            return value
        
        return "None"

    def _extract_multi_option_selection(self, variable_name: str, before_context: str, 
                                       after_context: str, final_content: str) -> Tuple[str, float]:
        """
        Extract which option was actually selected from multi-option variables.
        
        For variables like [Select one of the following: (your copayment) OR (your coinsurance amount) OR (your copayment or coinsurance amount)]
        This method finds which option was actually chosen in the source document.
        """
        try:
            var_lower = variable_name.lower()
            content_lower = final_content.lower()
            
            # Extract options from the variable name
            options = self._extract_options_from_variable(variable_name)
            if not options:
                return "None", 0.0
            
            # Look for each option in the source content
            best_match = None
            best_confidence = 0.0
            
            for option in options:
                # Clean the option text (remove parentheses, etc.)
                clean_option = re.sub(r'[()]', '', option).strip()
                if not clean_option:
                    continue
                
                # Create patterns to find this option in context
                option_patterns = [
                    # Direct match
                    rf'\b{re.escape(clean_option)}\b',
                    # With surrounding context
                    rf'{re.escape(before_context.lower())}\s*{re.escape(clean_option)}\s*{re.escape(after_context.lower())}',
                    # Partial match for longer options
                    rf'\b{re.escape(clean_option.split()[0])}.*?{re.escape(clean_option.split()[-1])}\b' if len(clean_option.split()) > 1 else None
                ]
                
                for pattern in option_patterns:
                    if not pattern:
                        continue
                    
                    matches = re.findall(pattern, content_lower, re.IGNORECASE)
                    if matches:
                        # Found the option in source
                        confidence = 0.9 if len(matches) == 1 else 0.7
                        if confidence > best_confidence:
                            best_match = clean_option
                            best_confidence = confidence
                            break
            
            # If no direct match found, try fuzzy matching
            if not best_match:
                best_match, best_confidence = self._fuzzy_match_options(options, final_content)
            
            return best_match, best_confidence
            
        except Exception as e:
            logger.warning(f"Error in multi-option extraction: {e}")
            return "None", 0.0
    
    def _extract_options_from_variable(self, variable_name: str) -> List[str]:
        """Extract individual options from a multi-option variable."""
        options = []
        
        # Pattern: [Select one of the following: option1 OR option2 OR option3]
        select_match = re.search(r'\[select\s+one\s+of\s+the\s+following:\s*([^\]]+)\]', variable_name, re.IGNORECASE)
        if select_match:
            options_text = select_match.group(1)
            # Split by OR
            raw_options = re.split(r'\s+OR\s+', options_text, flags=re.IGNORECASE)
            # Clean each option (remove parentheses and extra whitespace)
            for opt in raw_options:
                clean_opt = re.sub(r'[()]', '', opt.strip())
                if clean_opt:
                    options.append(clean_opt)
        
        # Pattern: [insert as applicable: option1 OR option2]
        applicable_match = re.search(r'\[insert\s+as\s+applicable:\s*([^\]]+)\]', variable_name, re.IGNORECASE)
        if applicable_match:
            options_text = applicable_match.group(1)
            raw_options = re.split(r'\s+OR\s+', options_text, flags=re.IGNORECASE)
            for opt in raw_options:
                clean_opt = re.sub(r'[()]', '', opt.strip())
                if clean_opt:
                    options.append(clean_opt)
        
        # Pattern: [insert X OR Y]
        or_match = re.search(r'\[insert\s+([^]]+\s+OR\s+[^]]+)\]', variable_name, re.IGNORECASE)
        if or_match and not select_match and not applicable_match:
            options_text = or_match.group(1)
            raw_options = re.split(r'\s+OR\s+', options_text, flags=re.IGNORECASE)
            for opt in raw_options:
                clean_opt = re.sub(r'[()]', '', opt.strip())
                if clean_opt:
                    options.append(clean_opt)
        
        return list(set(options))  # Remove duplicates
    
    def _fuzzy_match_options(self, options: List[str], content: str) -> Tuple[str, float]:
        """Use fuzzy matching to find the best option match in content."""
        import difflib
        
        best_match = None
        best_ratio = 0.0
        
        for option in options:
            # Clean the option
            clean_option = re.sub(r'[()]', '', option).strip()
            if not clean_option:
                continue
            
            # Find the best match in content
            words = content.split()
            for i in range(len(words) - len(clean_option.split()) + 1):
                phrase = ' '.join(words[i:i + len(clean_option.split())])
                ratio = difflib.SequenceMatcher(None, clean_option.lower(), phrase.lower()).ratio()
                
                if ratio > best_ratio and ratio > 0.6:  # Threshold for acceptable match
                    best_ratio = ratio
                    best_match = clean_option
        
        confidence = best_ratio if best_match else 0.0
        return best_match, confidence


# Test function
def test_simple_mapper():
    """Test the simple mapper with sample data."""
    print("🧪 Testing Simple Mapper")
    print("=" * 50)
    
    mapper = SimpleMapper()
    
    # Create test content
    model_content = "This plan, [insert 2025 plan name], is offered by [insert MAO name]."
    final_content = "This plan, Medicare Plus Blue Group PPO, is offered by Blue Cross Blue Shield of Michigan."
    
    # Test variable extraction
    print("Testing variable extraction...")
    variables = []
    
    # Simulate the variable extraction
    variable_matches = list(re.finditer(r'\[([^\]]+)\]', model_content))
    for match in variable_matches:
        var_name = match.group(1).strip()
        var_start, var_end = match.span()
        before_context = model_content[:var_start].strip()
        after_context = model_content[var_end:].strip()
        
        variables.append({
            'variable': var_name,
            'before_context': before_context.split()[-3:],  # Last 3 words
            'after_context': after_context.split()[:3]      # First 3 words
        })
    
    for var in variables:
        before = " ".join(var['before_context'])
        after = " ".join(var['after_context'])
        
        print(f"Variable: {var['variable']}")
        print(f"  Before: '{before}'")
        print(f"  After: '{after}'")
        
        # Test extraction
        value, confidence, method = mapper._extract_value(
            var['variable'], before, after, final_content
        )
        
        print(f"  Result: '{value}' ({method}, {confidence:.0%})")
        print()


if __name__ == "__main__":
    test_simple_mapper() 