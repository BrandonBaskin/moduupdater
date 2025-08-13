#!/usr/bin/env python3
"""
Enhanced Mapping with Timeout and Batch Processing
Prevents freezes by adding timeouts and batch processing for AI calls.
"""

import asyncio
import time
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from enhanced_mapping_integration import EnhancedMappingEngine
from logging_config import logger

class EnhancedMappingWithTimeout:
    """
    Enhanced mapping engine with timeout protection and batch processing.
    """
    
    def __init__(self, timeout_per_variable: int = 30, batch_size: int = 5):
        self.engine = EnhancedMappingEngine()
        self.timeout_per_variable = timeout_per_variable
        self.batch_size = batch_size
        self.processed_count = 0
        self.failed_variables = []
        
    def extract_variable_with_timeout(self, variable_name: str, variable_text: str, 
                                    context_before: str, context_after: str,
                                    source_paragraphs: List[str]) -> Tuple[str, float, str]:
        """
        Extract variable with timeout protection.
        """
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.engine.extract_variable_intelligently,
                    variable_name, variable_text, context_before, context_after, source_paragraphs
                )
                
                result = future.result(timeout=self.timeout_per_variable)
                self.processed_count += 1
                return result
                
        except FuturesTimeoutError:
            logger.warning(f"⏰ Timeout ({self.timeout_per_variable}s) for variable: {variable_name}")
            self.failed_variables.append(variable_name)
            return "None", 0.0, f"Timeout after {self.timeout_per_variable} seconds"
            
        except Exception as e:
            logger.error(f"❌ Error extracting variable {variable_name}: {e}")
            self.failed_variables.append(variable_name)
            return "None", 0.0, f"Error: {str(e)}"
    
    def process_variables_in_batches(self, variables_to_process: List[Dict], 
                                   source_paragraphs: List[str],
                                   progress_callback=None) -> List[Dict]:
        """
        Process variables in batches to prevent system overload.
        """
        results = []
        total_variables = len(variables_to_process)
        
        logger.info(f"🔄 Processing {total_variables} variables in batches of {self.batch_size}")
        
        for batch_start in range(0, total_variables, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_variables)
            batch = variables_to_process[batch_start:batch_end]
            
            logger.info(f"📦 Processing batch {batch_start//self.batch_size + 1}/{(total_variables-1)//self.batch_size + 1}")
            
            # Process batch
            batch_results = []
            for i, var_info in enumerate(batch):
                variable_name = var_info.get('variable_name', '')
                variable_text = var_info.get('variable_text', '')
                context_before = var_info.get('context_before', '')
                context_after = var_info.get('context_after', '')
                
                if progress_callback:
                    overall_progress = ((batch_start + i) / total_variables) * 100
                    progress_callback(overall_progress)
                
                # Extract with timeout
                extracted_value, confidence, reasoning = self.extract_variable_with_timeout(
                    variable_name, variable_text, context_before, context_after, source_paragraphs
                )
                
                result = {
                    'variable': variable_name,
                    'extracted_value': extracted_value,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'source': 'enhanced_ai_extraction_timeout',
                    'batch_number': batch_start // self.batch_size + 1
                }
                
                batch_results.append(result)
                
                # Small delay between variables to prevent overwhelming
                time.sleep(0.5)
            
            results.extend(batch_results)
            
            # Longer delay between batches
            if batch_end < total_variables:
                logger.info(f"⏸️  Batch complete. Resting for 2 seconds...")
                time.sleep(2)
        
        # Final summary
        success_count = len([r for r in results if r['extracted_value'] != 'None'])
        logger.info(f"📊 Batch processing complete: {success_count}/{total_variables} successful")
        logger.info(f"⏰ Timeout failures: {len(self.failed_variables)}")
        
        if self.failed_variables:
            logger.warning(f"⚠️  Failed variables: {', '.join(self.failed_variables[:5])}{'...' if len(self.failed_variables) > 5 else ''}")
        
        return results

def create_enhanced_mapping_with_timeout(timeout_per_variable: int = 30, batch_size: int = 5) -> EnhancedMappingWithTimeout:
    """Create enhanced mapping engine with timeout protection."""
    return EnhancedMappingWithTimeout(timeout_per_variable, batch_size)


# Test function
if __name__ == "__main__":
    # Test the timeout protection
    engine = create_enhanced_mapping_with_timeout(timeout_per_variable=10, batch_size=2)
    
    test_variables = [
        {
            'variable_name': 'insert URL',
            'variable_text': '[insert URL]',
            'context_before': 'visit our website at',
            'context_after': 'for more information'
        },
        {
            'variable_name': 'insert plan name',
            'variable_text': '[insert plan name]', 
            'context_before': 'This plan,',
            'context_after': ', is offered by'
        }
    ]
    
    source_paragraphs = [
        "Visit our website at www.example.com for more information.",
        "This plan, Medicare Plus Blue PPO, is offered by Blue Cross Blue Shield."
    ]
    
    results = engine.process_variables_in_batches(test_variables, source_paragraphs)
    
    print("🎯 Test Results:")
    for result in results:
        print(f"  {result['variable']}: {result['extracted_value']} (confidence: {result['confidence']:.2f})")