#!/usr/bin/env python3
"""
Model-to-Model Variable Mapper
Intelligently maps variables between different model versions (e.g., 2025 → 2026)
Handles year updates, same variables, and complex relationships with AI agent support.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from docx import Document
from document_parser import DocumentParser

logger = logging.getLogger(__name__)

class ModelVariableMapper:
    """
    Maps variables between different model versions with intelligent heuristics and AI agent support.
    """
    
    def __init__(self):
        # Year mapping patterns
        self.year_patterns = {
            '2025': '2026',
            '2024': '2025',
            '2023': '2024'
        }
        
        # Variables that should remain the same across years
        self.static_variables = {
            'insert MAO name',
            'insert phone number',
            'insert TTY number',
            'insert days and hours of operation',
            'insert DBA names in parentheses, as applicable, after listing required MAO names',
            'insert DBA names in parentheses, as applicable, after listing required MAO names throughout this document'
        }
        
        # Variables that need year updates
        self.year_variables = {
            'insert 2025 plan name': 'insert 2026 plan name',
            'insert 2024 plan name': 'insert 2025 plan name',
            'insert 2023 plan name': 'insert 2024 plan name',
            '2025 EOC model': '2026 EOC model',
            '2024 EOC model': '2025 EOC model',
            '2023 EOC model': '2024 EOC model'
        }
        
        # Complex variable relationships
        self.variable_relationships = {
            'insert plan type': 'insert plan type',  # Same across years
            'insert languages that meet the 5% threshold': 'insert languages that meet the 5% threshold',
            'Plans must insert language about availability of alternate formats (e.g., braille, large print, audio) as applicable.': 
                'Plans must insert language about availability of alternate formats (e.g., braille, large print, audio) as applicable.',
            'Remove terms as needed to reflect plan benefits': 'Remove terms as needed to reflect plan benefits'
        }
    
    def extract_variables_from_model(self, model_path: str) -> List[Dict]:
        """
        Extract all variables from a model document with their context.
        """
        try:
            parser = DocumentParser()
            blocks = parser.parse(model_path)
            
            variables = []
            for block in blocks:
                if block.get('type') == 'variable':
                    var_name = block.get('inner_text', '').strip()
                    var_text = block.get('text', '')
                    para_idx = block.get('para_idx', 0)
                    
                    if var_name:
                        variables.append({
                            'name': var_name,
                            'text': var_text,
                            'para_idx': para_idx,
                            'block': block
                        })
            
            logger.info(f"Extracted {len(variables)} variables from {model_path}")
            return variables
            
        except Exception as e:
            logger.error(f"Error extracting variables from {model_path}: {e}")
            return []
    
    def map_variables_between_models(self, 
                                   old_model_path: str, 
                                   new_model_path: str,
                                   log_callback: callable = None,
                                   progress_callback: callable = None) -> Dict[str, str]:
        """
        Map variables from old model to new model with intelligent heuristics and AI agent support.
        Returns mapping of old_variable_name -> new_variable_name
        """
        if log_callback is None:
            log_callback = lambda x: logger.info(x)
        if progress_callback is None:
            progress_callback = lambda x: None
        
        log_callback("🧠 Starting intelligent model-to-model variable mapping with AI agent...")
        
        # Extract variables from both models
        old_variables = self.extract_variables_from_model(old_model_path)
        new_variables = self.extract_variables_from_model(new_model_path)
        
        log_callback(f"📊 Old model: {len(old_variables)} variables")
        log_callback(f"📊 New model: {len(new_variables)} variables")
        
        # Create mapping with progress tracking
        variable_mapping = {}
        total_strategies = 5
        current_strategy = 0
        
        # Strategy 1: Direct year mapping
        current_strategy += 1
        progress_callback((current_strategy / total_strategies) * 100)
        log_callback("🎯 Strategy 1: Direct year mapping...")
        year_mappings = 0
        for old_var in old_variables:
            old_name = old_var['name']
            
            # Check for year updates
            for old_year, new_year in self.year_patterns.items():
                if old_year in old_name:
                    new_name = old_name.replace(old_year, new_year)
                    if any(new_name == new_var['name'] for new_var in new_variables):
                        variable_mapping[old_name] = new_name
                        year_mappings += 1
                        log_callback(f"✅ Year update: '{old_name}' → '{new_name}'")
                        break
        log_callback(f"📊 Year mappings: {year_mappings}")
        
        # Strategy 2: Static variables (same across years)
        current_strategy += 1
        progress_callback((current_strategy / total_strategies) * 100)
        log_callback("🎯 Strategy 2: Static variables...")
        static_mappings = 0
        for old_var in old_variables:
            old_name = old_var['name']
            if old_name in self.static_variables:
                if any(old_name == new_var['name'] for new_var in new_variables):
                    variable_mapping[old_name] = old_name
                    static_mappings += 1
                    log_callback(f"✅ Static variable: '{old_name}' (unchanged)")
        log_callback(f"📊 Static mappings: {static_mappings}")
        
        # Strategy 3: Known variable relationships
        current_strategy += 1
        progress_callback((current_strategy / total_strategies) * 100)
        log_callback("🎯 Strategy 3: Known relationships...")
        known_mappings = 0
        for old_var in old_variables:
            old_name = old_var['name']
            if old_name in self.variable_relationships:
                new_name = self.variable_relationships[old_name]
                if any(new_name == new_var['name'] for new_var in new_variables):
                    variable_mapping[old_name] = new_name
                    known_mappings += 1
                    log_callback(f"✅ Known relationship: '{old_name}' → '{new_name}'")
        log_callback(f"📊 Known mappings: {known_mappings}")
        
        # Strategy 4: AI Agent enhanced fuzzy matching
        current_strategy += 1
        progress_callback((current_strategy / total_strategies) * 100)
        log_callback("🎯 Strategy 4: AI Agent enhanced fuzzy matching...")
        fuzzy_mappings = 0
        remaining_old = [v for v in old_variables if v['name'] not in variable_mapping]
        remaining_new = [v for v in new_variables if v['name'] not in variable_mapping.values()]
        
        # Use AI agent for complex matching
        ai_mappings = self._ai_enhanced_mapping(remaining_old, remaining_new, log_callback)
        for old_name, new_name in ai_mappings.items():
            variable_mapping[old_name] = new_name
            fuzzy_mappings += 1
            log_callback(f"🤖 AI match: '{old_name}' → '{new_name}'")
        
        # Fallback to traditional fuzzy matching
        for old_var in remaining_old:
            if old_var['name'] not in variable_mapping:
                old_name = old_var['name']
                best_match = self._find_best_fuzzy_match(old_name, [v['name'] for v in remaining_new])
                if best_match:
                    variable_mapping[old_name] = best_match
                    fuzzy_mappings += 1
                    log_callback(f"🔍 Fuzzy match: '{old_name}' → '{best_match}'")
        
        log_callback(f"📊 Fuzzy mappings: {fuzzy_mappings}")
        
        # Strategy 5: Validation and quality check
        current_strategy += 1
        progress_callback((current_strategy / total_strategies) * 100)
        log_callback("🎯 Strategy 5: Validation and quality check...")
        
        # Calculate success statistics
        total_old_vars = len(old_variables)
        total_new_vars = len(new_variables)
        mapped_vars = len(variable_mapping)
        coverage_rate = (mapped_vars / total_old_vars * 100) if total_old_vars > 0 else 0
        
        log_callback(f"📊 Mapping Statistics:")
        log_callback(f"   • Total old variables: {total_old_vars}")
        log_callback(f"   • Total new variables: {total_new_vars}")
        log_callback(f"   • Successfully mapped: {mapped_vars}")
        log_callback(f"   • Coverage rate: {coverage_rate:.1f}%")
        log_callback(f"   • Year mappings: {year_mappings}")
        log_callback(f"   • Static mappings: {static_mappings}")
        log_callback(f"   • Known mappings: {known_mappings}")
        log_callback(f"   • AI/Fuzzy mappings: {fuzzy_mappings}")
        
        return variable_mapping
    
    def _ai_enhanced_mapping(self, old_variables: List[Dict], new_variables: List[Dict], 
                            log_callback: callable) -> Dict[str, str]:
        """
        Use AI agent to enhance variable mapping for complex cases.
        """
        try:
            from logic_mapper_llm import LogicMapper
            mapper = LogicMapper()
            
            mappings = {}
            log_callback("🤖 AI Agent analyzing variable similarities...")
            
            for old_var in old_variables[:20]:  # Limit to prevent too many API calls
                old_name = old_var['name']
                old_context = old_var.get('text', '')
                
                # Create a prompt for the AI to find the best match
                prompt = f"""
                Given this variable from the old model:
                Variable: "{old_name}"
                Context: "{old_context[:200]}..."
                
                Which of these variables from the new model is most similar?
                {chr(10).join([f"- {v['name']}" for v in new_variables[:10]])}
                
                Respond with just the variable name that best matches, or "NONE" if no good match exists.
                """
                
                try:
                    response = mapper._call_llm(prompt, max_tokens=50)
                    if response and response.strip() != "NONE":
                        # Find the matching variable
                        for new_var in new_variables:
                            if new_var['name'] in response:
                                mappings[old_name] = new_var['name']
                                break
                except Exception as e:
                    log_callback(f"⚠️ AI mapping error for '{old_name}': {e}")
                    continue
            
            return mappings
            
        except Exception as e:
            log_callback(f"⚠️ AI enhanced mapping not available: {e}")
            return {}
    
    def _find_best_fuzzy_match(self, old_name: str, new_names: List[str]) -> Optional[str]:
        """
        Find the best fuzzy match for a variable name.
        """
        try:
            from fuzzywuzzy import process
            if not new_names:
                return None
            
            # Clean the names for better matching
            old_clean = self._clean_variable_name(old_name)
            new_cleans = [self._clean_variable_name(name) for name in new_names]
            
            # Find best match
            match, score = process.extractOne(old_clean, new_cleans)
            
            if score > 70:  # Good match threshold
                # Return the original name that corresponds to the cleaned match
                for i, clean_name in enumerate(new_cleans):
                    if clean_name == match:
                        return new_names[i]
            
            return None
            
        except ImportError:
            logger.warning("fuzzywuzzy not available for fuzzy matching")
            return None
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return None
    
    def _clean_variable_name(self, name: str) -> str:
        """
        Clean variable name for better matching.
        """
        # Remove common prefixes/suffixes
        cleaned = name.lower()
        cleaned = re.sub(r'^insert\s+', '', cleaned)
        cleaned = re.sub(r'^\d{4}\s+', '', cleaned)  # Remove years
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def create_wizard_suggestions(self,
                                variable_mapping: Dict[str, str],
                                extracted_values: Dict[str, str],
                                log_callback: callable = None) -> Dict[str, str]:
        """
        Create wizard suggestions based on model mapping and extracted values.
        Returns mapping of new_variable_name -> suggestion_value
        """
        if log_callback is None:
            log_callback = lambda x: logger.info(x)
        
        log_callback("🎯 Creating wizard suggestions from model mapping...")
        
        # Create suggestions
        suggestions = {}
        
        for old_var, new_var in variable_mapping.items():
            if old_var in extracted_values:
                value = extracted_values[old_var]
                if value and value.strip():
                    # Handle year updates in the value itself
                    updated_value = self._update_value_for_year(value, old_var, new_var)
                    suggestions[new_var] = updated_value
                    log_callback(f"💡 Suggestion for '{new_var}': '{updated_value}' (from '{old_var}')")
        
        # Add static suggestions for common variables
        static_suggestions = self._get_static_suggestions()
        for var_name, suggestion in static_suggestions.items():
            if var_name not in suggestions:
                suggestions[var_name] = suggestion
                log_callback(f"💡 Static suggestion for '{var_name}': '{suggestion}'")
        
        # Add intelligent suggestions for year-specific variables
        year_suggestions = self._get_year_specific_suggestions()
        for var_name, suggestion in year_suggestions.items():
            if var_name not in suggestions:
                suggestions[var_name] = suggestion
                log_callback(f"💡 Year-specific suggestion for '{var_name}': '{suggestion}'")
        
        log_callback(f"📊 Created {len(suggestions)} wizard suggestions")
        return suggestions
    
    def _update_value_for_year(self, value: str, old_var: str, new_var: str) -> str:
        """
        Update a value to reflect year changes (e.g., 2025 -> 2026).
        """
        # Handle year updates in values
        year_updates = {
            '2025': '2026',
            '2024': '2025',
            '2023': '2024'
        }
        
        updated_value = value
        for old_year, new_year in year_updates.items():
            if old_year in value:
                updated_value = value.replace(old_year, new_year)
                break
        
        # Handle specific plan name updates
        if 'plan name' in old_var.lower() and 'plan name' in new_var.lower():
            if 'Medicare & You' in updated_value:
                updated_value = 'Medicare Plus Blue PPO'
            elif '2025' in old_var and '2026' in new_var:
                # Update plan names for new year
                if 'Medicare' in updated_value:
                    updated_value = updated_value.replace('2025', '2026')
        
        return updated_value
    
    def _get_static_suggestions(self) -> Dict[str, str]:
        """
        Get static suggestions for common variables.
        """
        return {
            'insert phone number': '1-855-669-8040',
            'insert TTY number': '711',
            'insert days and hours of operation': 'Monday through Friday, 8 a.m. to 8 p.m.',
            'Plans must insert language about availability of alternate formats (e.g., braille, large print, audio) as applicable.': 
                'This document is available in alternate formats such as braille, large print, and audio upon request.'
        }
    
    def _get_year_specific_suggestions(self) -> Dict[str, str]:
        """
        Get year-specific suggestions for common variables.
        """
        return {
            'insert 2026 plan name': 'Medicare Plus Blue PPO',
            'insert 2025 plan name': 'Medicare Plus Blue PPO',
            'insert 2024 plan name': 'Medicare Plus Blue PPO',
            '2026 EOC model': '2026 EOC model',
            '2025 EOC model': '2025 EOC model',
            '2024 EOC model': '2024 EOC model'
        }
    
    def validate_mapping(self, mapping: Dict[str, str], 
                        old_model_path: str, 
                        new_model_path: str) -> Dict[str, any]:
        """
        Validate the quality of the model mapping.
        Returns validation results with scores and recommendations.
        """
        try:
            # Extract variables from both models
            old_variables = self.extract_variables_from_model(old_model_path)
            new_variables = self.extract_variables_from_model(new_model_path)
            
            # Calculate validation metrics
            total_old_vars = len(old_variables)
            total_new_vars = len(new_variables)
            mapped_vars = len(mapping)
            
            # Coverage metrics
            coverage_rate = (mapped_vars / total_old_vars * 100) if total_old_vars > 0 else 0
            
            # Quality metrics
            year_mappings = sum(1 for old, new in mapping.items() if any(year in old for year in self.year_patterns))
            static_mappings = sum(1 for old, new in mapping.items() if old in self.static_variables)
            known_mappings = sum(1 for old, new in mapping.items() if old in self.variable_relationships)
            
            # Calculate quality score (0-100)
            quality_score = 0
            if total_old_vars > 0:
                # Year mappings are high quality
                quality_score += (year_mappings / total_old_vars) * 40
                # Static mappings are high quality
                quality_score += (static_mappings / total_old_vars) * 30
                # Known mappings are medium quality
                quality_score += (known_mappings / total_old_vars) * 20
                # Coverage bonus
                quality_score += min(coverage_rate / 100, 1) * 10
            
            # Overall score
            overall_score = (coverage_rate + quality_score) / 2
            
            # Generate recommendations
            recommendations = []
            if coverage_rate < 70:
                recommendations.append("Low coverage rate - consider manual review of unmapped variables")
            if quality_score < 50:
                recommendations.append("Low quality mappings - review fuzzy matches and AI suggestions")
            if year_mappings < total_old_vars * 0.3:
                recommendations.append("Few year-based mappings - check for year pattern updates")
            
            validation_results = {
                'overall_score': round(overall_score, 1),
                'coverage_rate': round(coverage_rate, 1),
                'quality_score': round(quality_score, 1),
                'total_old_variables': total_old_vars,
                'total_new_variables': total_new_vars,
                'mapped_variables': mapped_vars,
                'year_mappings': year_mappings,
                'static_mappings': static_mappings,
                'known_mappings': known_mappings,
                'recommendations': recommendations,
                'status': 'good' if overall_score >= 70 else 'needs_review' if overall_score >= 50 else 'poor'
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating mapping: {e}")
            return {
                'overall_score': 0,
                'coverage_rate': 0,
                'quality_score': 0,
                'error': str(e),
                'status': 'error'
            } 