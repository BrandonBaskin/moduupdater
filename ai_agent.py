#!/usr/bin/env python3
"""
Robust AI Agent for intelligent variable extraction using context understanding.
Uses Ollama/Llama3 with carefully crafted prompts.
"""

import requests
import json
import time
import re
from typing import Dict, List, Tuple, Optional
from logging_config import logger


class RobustAIAgent:
    """AI Agent with robust context understanding for variable extraction."""
    
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def extract_variable_with_context(self, variable_name: str, model_context: str, 
                                    source_document: str) -> Tuple[str, float, str]:
        """
        Use AI to intelligently extract variable values using context understanding.
        
        Args:
            variable_name: The variable to extract (e.g., "insert 2026 plan name")
            model_context: Context from model document around the variable
            source_document: The source document content to extract from
            
        Returns:
            Tuple of (extracted_value, confidence, reasoning)
        """
        try:
            # Create a robust prompt for the AI
            prompt = self._create_extraction_prompt(variable_name, model_context, source_document)
            
            # Call the AI model
            response = self._call_ollama(prompt)
            
            if response:
                # Parse the AI response
                extracted_value, confidence, reasoning = self._parse_ai_response(response, variable_name)
                return extracted_value, confidence, reasoning
            else:
                return "None", 0.0, "AI model not available"
                
        except Exception as e:
            logger.error(f"Error in AI extraction: {e}")
            return "None", 0.0, f"Error: {e}"
    
    def _create_extraction_prompt(self, variable_name: str, model_context: str, source_document: str) -> str:
        """Create a robust, detailed prompt for the AI model."""
        
        # Classify the variable type for better prompting
        var_type = self._classify_variable_type(variable_name)
        
        # Base prompt with clear instructions
        prompt = f"""You are an expert document analyst. Your task is to extract specific variable values from a source document using context clues.

VARIABLE TO EXTRACT: [{variable_name}]
VARIABLE TYPE: {var_type}
MODEL CONTEXT: {model_context}

INSTRUCTIONS:
1. Analyze the MODEL CONTEXT to understand what surrounds the variable
2. Find similar context patterns in the SOURCE DOCUMENT below
3. Extract the exact value that would replace the variable
4. Be precise - extract only the specific value, not extra words
5. Use the surrounding words as clues to locate the correct value

EXAMPLE PATTERNS:
- If context is "This plan, [variable], is offered by" → look for "This plan, VALUE, is offered by"
- If context is "Call [variable] for help" → look for "Call VALUE for help"
- If context is "[variable] may apply" → look for "VALUE may apply"

SPECIFIC RULES FOR VARIABLE TYPES:
"""

        # Add specific rules based on variable type
        if var_type == "plan_name":
            prompt += """
- Plan names are usually capitalized (e.g., "Medicare Plus Blue Group PPO")
- Look for patterns with "Medicare", "Plus", "Blue", "PPO", "HMO", "Group"
- Extract the full plan name including all parts
"""
        elif var_type == "organization":
            prompt += """
- Organization names are multiple capitalized words
- Look for patterns like "Blue Cross Blue Shield of [State]"
- Include full organization name with all parts
"""
        elif var_type == "phone_number":
            prompt += """
- Phone numbers follow patterns like "1-800-XXX-XXXX" or "(800) XXX-XXXX"
- Extract the complete phone number including formatting
"""
        elif var_type == "tty_number":
            prompt += """
- TTY numbers are usually "711" - this is the standard
- Look for "TTY 711" or just "711" in telecommunications context
"""
        elif var_type == "removal_instruction":
            prompt += """
- These refer to terms that can be removed/modified
- Look for lists like "benefits, premiums, copayments, coinsurance"
- Extract the complete list of terms mentioned
"""

        prompt += f"""

SOURCE DOCUMENT:
{source_document[:3000]}...

RESPONSE FORMAT:
You must respond with EXACTLY this format:
EXTRACTED_VALUE: [the exact value you found]
CONFIDENCE: [number from 0.0 to 1.0]
REASONING: [brief explanation of how you found it]

IMPORTANT:
- If you cannot find the value, respond with "EXTRACTED_VALUE: None"
- Be conservative with confidence - only use >0.8 if you're very sure
- Focus on the context clues to locate the correct value
- Extract only the value, not surrounding words

BEGIN EXTRACTION:"""

        return prompt
    
    def _classify_variable_type(self, variable_name: str) -> str:
        """Classify the variable type for better AI prompting."""
        var_lower = variable_name.lower()
        
        if 'plan name' in var_lower:
            return "plan_name"
        elif 'mao name' in var_lower or 'organization' in var_lower:
            return "organization"
        elif 'phone' in var_lower:
            return "phone_number"
        elif 'tty' in var_lower:
            return "tty_number"
        elif 'remove terms' in var_lower or 'remove' in var_lower:
            return "removal_instruction"
        elif 'address' in var_lower:
            return "address"
        elif 'date' in var_lower or 'day' in var_lower or 'month' in var_lower:
            return "date_time"
        elif 'premium' in var_lower or 'cost' in var_lower or 'amount' in var_lower:
            return "financial"
        elif 'state' in var_lower or 'county' in var_lower or 'zip' in var_lower:
            return "location"
        else:
            return "general"
    
    def _call_ollama(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call the Ollama API with robust error handling."""
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent extractions
                        "top_p": 0.9,
                        "num_predict": 200   # Limit response length
                    }
                }
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('response', '').strip()
                else:
                    logger.warning(f"Ollama API error {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ollama connection error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
        
        return None
    
    def _parse_ai_response(self, response: str, variable_name: str) -> Tuple[str, float, str]:
        """Parse the AI model's response into structured data."""
        try:
            # Initialize defaults
            extracted_value = "None"
            confidence = 0.0
            reasoning = "Could not parse AI response"
            
            # Parse the structured response
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('EXTRACTED_VALUE:'):
                    extracted_value = line.replace('EXTRACTED_VALUE:', '').strip()
                    if extracted_value.lower() in ['none', 'null', 'n/a', '']:
                        extracted_value = "None"
                
                elif line.startswith('CONFIDENCE:'):
                    conf_str = line.replace('CONFIDENCE:', '').strip()
                    try:
                        confidence = float(conf_str)
                        confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                    except ValueError:
                        confidence = 0.5
                
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
            
            # Post-process the extracted value
            if extracted_value != "None":
                extracted_value = self._clean_extracted_value(extracted_value, variable_name)
            
            # Log the extraction
            logger.info(f"AI Extraction: [{variable_name}] → '{extracted_value}' (confidence: {confidence:.2f})")
            
            return extracted_value, confidence, reasoning
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return "None", 0.0, f"Parse error: {e}"
    
    def _clean_extracted_value(self, value: str, variable_name: str) -> str:
        """Clean and format the extracted value."""
        if not value or value.lower() in ['none', 'null', 'n/a']:
            return "None"
        
        # Remove quotes and extra whitespace
        value = value.strip(' "\'\n\t')
        
        # Remove common prefixes that the AI might include
        prefixes_to_remove = [
            'the value is:', 'value:', 'answer:', 'result:', 'extracted:',
            'found:', 'located:', 'identified:'
        ]
        
        value_lower = value.lower()
        for prefix in prefixes_to_remove:
            if value_lower.startswith(prefix):
                value = value[len(prefix):].strip()
                break
        
        # Variable-specific cleaning
        var_lower = variable_name.lower()
        
        if 'plan name' in var_lower:
            # Capitalize plan names properly
            value = self._format_plan_name(value)
        
        elif 'phone' in var_lower:
            # Format phone numbers
            value = self._format_phone_number(value)
        
        elif 'tty' in var_lower:
            # Clean TTY numbers
            if '711' in value:
                value = "711"
        
        return value
    
    def _format_plan_name(self, plan_name: str) -> str:
        """Format plan names with proper capitalization."""
        if not plan_name or plan_name == "None":
            return plan_name
        
        # Split into words and capitalize appropriately
        words = plan_name.split()
        formatted_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in ['ppo', 'hmo', 'pos']:
                formatted_words.append(word_lower.upper())
            elif word_lower in ['of', 'and', 'the', 'a', 'an']:
                formatted_words.append(word_lower)
            else:
                formatted_words.append(word.capitalize())
        
        return " ".join(formatted_words)
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone numbers consistently."""
        if not phone or phone == "None":
            return phone
        
        # Extract just the digits
        digits = re.sub(r'[^\d]', '', phone)
        
        # Format as 1-XXX-XXX-XXXX if we have 11 digits starting with 1
        if len(digits) == 11 and digits.startswith('1'):
            return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
        
        # Format as XXX-XXX-XXXX if we have 10 digits
        elif len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        
        # Return as-is if format doesn't match
        return phone
    
    def test_extraction(self):
        """Test the AI agent with sample data."""
        print("🧪 Testing AI Agent")
        print("=" * 50)
        
        test_cases = [
            {
                'variable': 'insert 2025 plan name',
                'context': 'This plan, [insert 2025 plan name], is offered by',
                'source': 'This plan, Medicare Plus Blue Group PPO, is offered by Blue Cross Blue Shield of Michigan.'
            },
            {
                'variable': 'insert TTY number',
                'context': 'Call [insert phone number] or TTY [insert TTY number] for help',
                'source': 'Call 1-855-669-8040 or TTY 711 for help with your questions.'
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"Test {i}: {test['variable']}")
            print(f"Context: {test['context']}")
            print(f"Source: {test['source']}")
            
            value, confidence, reasoning = self.extract_variable_with_context(
                test['variable'], test['context'], test['source']
            )
            
            print(f"Result: '{value}' (confidence: {confidence:.2f})")
            print(f"Reasoning: {reasoning}")
            print()


if __name__ == "__main__":
    agent = RobustAIAgent()
    agent.test_extraction() 