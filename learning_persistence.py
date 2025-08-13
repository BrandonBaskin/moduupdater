#!/usr/bin/env python3
"""
Learning Persistence System
Saves and loads the AI agent's learning progress for persistent knowledge.
Enhanced with training data management and improved statistics.
"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, List, Any
from logging_config import logger
import re

class LearningPersistence:
    """Manages persistent storage of the AI agent's learning progress."""
    
    def __init__(self, learning_dir: str = "learning_data"):
        self.learning_dir = learning_dir
        self.patterns_file = os.path.join(learning_dir, "learned_patterns.json")
        self.history_file = os.path.join(learning_dir, "extraction_history.json")
        self.confidence_file = os.path.join(learning_dir, "confidence_scores.json")
        self.metadata_file = os.path.join(learning_dir, "learning_metadata.json")
        self.training_data_file = os.path.join(learning_dir, "training_data.json")
        self.knowledge_base_file = os.path.join(learning_dir, "knowledge_base.json")
        
        # Ensure learning directory exists
        os.makedirs(learning_dir, exist_ok=True)
    
    def save_learning_state(self, learner) -> bool:
        """Save the current learning state to persistent storage."""
        try:
            # Save patterns
            patterns_data = {
                'patterns': learner.patterns,
                'last_updated': datetime.now().isoformat(),
                'total_examples': sum(len(info['examples']) for info in learner.patterns.values())
            }
            
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
            
            # Save extraction history
            history_data = {
                'extractions': learner.extraction_history if hasattr(learner, 'extraction_history') else [],
                'last_updated': datetime.now().isoformat(),
                'total_extractions': len(learner.extraction_history) if hasattr(learner, 'extraction_history') else 0
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
            # Save confidence scores
            confidence_data = {
                'confidence_scores': getattr(learner, 'confidence_scores', {}),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.confidence_file, 'w', encoding='utf-8') as f:
                json.dump(confidence_data, f, indent=2, ensure_ascii=False)
            
            # Save training data
            training_data = self._create_training_data(learner)
            with open(self.training_data_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            # Save knowledge base
            knowledge_base = self._create_knowledge_base(learner)
            with open(self.knowledge_base_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata = {
                'version': '2.0',
                'created': datetime.now().isoformat(),
                'last_save': datetime.now().isoformat(),
                'total_patterns': len(learner.patterns),
                'total_examples': sum(len(info['examples']) for info in learner.patterns.values()),
                'variable_types': list(learner.patterns.keys()),
                'training_data_size': len(training_data),
                'knowledge_base_size': len(knowledge_base)
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Learning state saved successfully. {metadata['total_examples']} examples stored.")
            logger.info(f"Training data: {len(training_data)} entries, Knowledge base: {len(knowledge_base)} entries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save learning state: {e}")
            return False
    
    def _create_training_data(self, learner) -> List[Dict]:
        """Create training data from learned patterns."""
        training_data = []
        
        try:
            for var_type, pattern_info in learner.patterns.items():
                if 'examples' in pattern_info:
                    for example in pattern_info['examples']:
                        training_entry = {
                            'variable_name': example.get('variable_name', ''),
                            'variable_type': var_type,
                            'extracted_value': example.get('extracted_value', ''),
                            'context': example.get('context', ''),
                            'source_paragraph': example.get('source_paragraph', ''),
                            'confidence': example.get('confidence', 0.0),
                            'timestamp': example.get('timestamp', datetime.now().isoformat()),
                            'success_rate': pattern_info.get('success_rate', 0.0)
                        }
                        training_data.append(training_entry)
            
            logger.info(f"Created {len(training_data)} training data entries")
            return training_data
            
        except Exception as e:
            logger.error(f"Error creating training data: {e}")
            return []
    
    def _create_knowledge_base(self, learner) -> Dict[str, Any]:
        """Create knowledge base from learned patterns and confidence scores."""
        knowledge_base = {
            'variable_types': {},
            'common_patterns': {},
            'confidence_thresholds': {},
            'extraction_rules': {},
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            # Analyze variable types
            for var_type, pattern_info in learner.patterns.items():
                if 'examples' in pattern_info:
                    examples = pattern_info['examples']
                    knowledge_base['variable_types'][var_type] = {
                        'count': len(examples),
                        'success_rate': pattern_info.get('success_rate', 0.0),
                        'common_values': self._get_common_values(examples),
                        'extraction_patterns': self._get_extraction_patterns(examples)
                    }
            
            # Analyze common patterns
            all_examples = []
            for pattern_info in learner.patterns.values():
                if 'examples' in pattern_info:
                    all_examples.extend(pattern_info['examples'])
            
            knowledge_base['common_patterns'] = self._analyze_common_patterns(all_examples)
            
            # Set confidence thresholds based on variable types
            knowledge_base['confidence_thresholds'] = {
                'input': 0.7,
                'option_select': 0.8,
                'conditional': 0.6,
                'static': 0.9,
                'unknown': 0.5
            }
            
            # Create extraction rules
            knowledge_base['extraction_rules'] = self._create_extraction_rules(learner)
            
            logger.info(f"Created knowledge base with {len(knowledge_base['variable_types'])} variable types")
            return knowledge_base
            
        except Exception as e:
            logger.error(f"Error creating knowledge base: {e}")
            return knowledge_base
    
    def _get_common_values(self, examples: List[Dict]) -> Dict[str, int]:
        """Get common values from examples."""
        value_counts = {}
        for example in examples:
            value = example.get('extracted_value', '')
            if value and value != 'None':
                value_counts[value] = value_counts.get(value, 0) + 1
        return dict(sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _get_extraction_patterns(self, examples: List[Dict]) -> List[Dict]:
        """Get extraction patterns from examples."""
        patterns = []
        for example in examples:
            pattern = {
                'variable_name': example.get('variable_name', ''),
                'context_length': len(example.get('context', '')),
                'has_numbers': any(char.isdigit() for char in example.get('extracted_value', '')),
                'has_special_chars': any(char in '.,;:!?' for char in example.get('extracted_value', '')),
                'confidence': example.get('confidence', 0.0)
            }
            patterns.append(pattern)
        return patterns
    
    def _analyze_common_patterns(self, examples: List[Dict]) -> Dict[str, Any]:
        """Analyze common patterns across all examples."""
        patterns = {
            'high_confidence_extractions': [],
            'common_context_lengths': [],
            'frequent_variable_names': [],
            'successful_extraction_techniques': []
        }
        
        try:
            # High confidence extractions
            high_conf = [ex for ex in examples if ex.get('confidence', 0) > 0.8]
            patterns['high_confidence_extractions'] = [
                {
                    'variable_name': ex.get('variable_name', ''),
                    'confidence': ex.get('confidence', 0),
                    'technique': 'ai_enhanced'
                } for ex in high_conf[:10]
            ]
            
            # Common context lengths
            context_lengths = [len(ex.get('context', '')) for ex in examples]
            if context_lengths:
                avg_length = sum(context_lengths) / len(context_lengths)
                patterns['common_context_lengths'] = {
                    'average': avg_length,
                    'min': min(context_lengths),
                    'max': max(context_lengths)
                }
            
            # Frequent variable names
            var_names = [ex.get('variable_name', '') for ex in examples]
            var_counts = {}
            for name in var_names:
                var_counts[name] = var_counts.get(name, 0) + 1
            patterns['frequent_variable_names'] = [
                {'name': name, 'count': count} 
                for name, count in sorted(var_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Successful extraction techniques
            patterns['successful_extraction_techniques'] = [
                'context_aware_extraction',
                'ai_enhanced_mapping',
                'pattern_based_learning',
                'confidence_scoring'
            ]
            
        except Exception as e:
            logger.error(f"Error analyzing common patterns: {e}")
        
        return patterns
    
    def _create_extraction_rules(self, learner) -> Dict[str, Any]:
        """Create extraction rules based on learned patterns."""
        rules = {
            'variable_type_rules': {},
            'confidence_rules': {},
            'context_rules': {}
        }
        
        try:
            # Rules for different variable types
            rules['variable_type_rules'] = {
                'input': {
                    'priority': 'high',
                    'technique': 'ai_enhanced',
                    'confidence_threshold': 0.7
                },
                'option_select': {
                    'priority': 'medium',
                    'technique': 'pattern_matching',
                    'confidence_threshold': 0.8
                },
                'conditional': {
                    'priority': 'medium',
                    'technique': 'context_analysis',
                    'confidence_threshold': 0.6
                },
                'static': {
                    'priority': 'low',
                    'technique': 'direct_mapping',
                    'confidence_threshold': 0.9
                }
            }
            
            # Confidence rules
            rules['confidence_rules'] = {
                'high_confidence': {'min': 0.8, 'action': 'accept'},
                'medium_confidence': {'min': 0.6, 'action': 'review'},
                'low_confidence': {'min': 0.0, 'action': 'reject'}
            }
            
            # Context rules
            rules['context_rules'] = {
                'min_context_length': 50,
                'max_context_length': 500,
                'preferred_context_ratio': 0.3
            }
            
        except Exception as e:
            logger.error(f"Error creating extraction rules: {e}")
        
        return rules
    
    def load_learning_state(self, learner) -> bool:
        """Load the learning state from persistent storage."""
        try:
            # Load patterns
            if os.path.exists(self.patterns_file):
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                    learner.patterns = patterns_data.get('patterns', {})
                    logger.info(f"Loaded {patterns_data.get('total_examples', 0)} learned examples")
            
            # Load extraction history
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    if hasattr(learner, 'extraction_history'):
                        learner.extraction_history = history_data.get('extractions', [])
                    logger.info(f"Loaded {history_data.get('total_extractions', 0)} extraction history entries")
            
            # Load confidence scores
            if os.path.exists(self.confidence_file):
                with open(self.confidence_file, 'r', encoding='utf-8') as f:
                    confidence_data = json.load(f)
                    if hasattr(learner, 'confidence_scores'):
                        learner.confidence_scores = confidence_data.get('confidence_scores', {})
            
            # Load training data
            if os.path.exists(self.training_data_file):
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                    logger.info(f"Loaded {len(training_data)} training data entries")
            
            # Load knowledge base
            if os.path.exists(self.knowledge_base_file):
                with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                    knowledge_base = json.load(f)
                    logger.info(f"Loaded knowledge base with {len(knowledge_base.get('variable_types', {}))} variable types")
            
            # Load metadata
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    logger.info(f"Learning system loaded: {metadata.get('total_examples', 0)} examples, {metadata.get('total_patterns', 0)} patterns")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load learning state: {e}")
            return False
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        try:
            stats = {
                'total_patterns': 0,
                'total_examples': 0,
                'total_extractions': 0,
                'avg_confidence': 0.0,
                'variable_types': {},
                'last_updated': 'Never',
                'training_data_size': 0,
                'knowledge_base_size': 0
            }
            
            # Load patterns
            if os.path.exists(self.patterns_file):
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                    stats['total_patterns'] = len(patterns_data.get('patterns', {}))
                    stats['total_examples'] = patterns_data.get('total_examples', 0)
                    stats['last_updated'] = patterns_data.get('last_updated', 'Never')
                    
                    # Count variable types
                    for var_type, pattern_info in patterns_data.get('patterns', {}).items():
                        if 'examples' in pattern_info:
                            stats['variable_types'][var_type] = len(pattern_info['examples'])
            
            # Load extraction history
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    stats['total_extractions'] = history_data.get('total_extractions', 0)
            
            # Load confidence scores
            if os.path.exists(self.confidence_file):
                with open(self.confidence_file, 'r', encoding='utf-8') as f:
                    confidence_data = json.load(f)
                    confidence_scores = confidence_data.get('confidence_scores', {})
                    if confidence_scores:
                        avg_conf = sum(score.get('confidence', 0) for score in confidence_scores.values()) / len(confidence_scores)
                        stats['avg_confidence'] = avg_conf
            
            # Load training data size
            if os.path.exists(self.training_data_file):
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                    stats['training_data_size'] = len(training_data)
            
            # Load knowledge base size
            if os.path.exists(self.knowledge_base_file):
                with open(self.knowledge_base_file, 'r', encoding='utf-8') as f:
                    knowledge_base = json.load(f)
                    stats['knowledge_base_size'] = len(knowledge_base.get('variable_types', {}))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting learning stats: {e}")
            return {
                'total_patterns': 0,
                'total_examples': 0,
                'total_extractions': 0,
                'avg_confidence': 0.0,
                'variable_types': {},
                'last_updated': 'Never',
                'training_data_size': 0,
                'knowledge_base_size': 0
            }
    
    def clear_learning_data(self) -> bool:
        """Clear all learning data."""
        try:
            files_to_remove = [
                self.patterns_file,
                self.history_file,
                self.confidence_file,
                self.metadata_file,
                self.training_data_file,
                self.knowledge_base_file
            ]
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed {file_path}")
            
            logger.info("All learning data cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing learning data: {e}")
            return False
    
    def export_training_data(self, output_path: str) -> bool:
        """Export training data to a file."""
        try:
            if os.path.exists(self.training_data_file):
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(training_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Training data exported to {output_path}")
                return True
            else:
                logger.warning("No training data available to export")
                return False
                
        except Exception as e:
            logger.error(f"Error exporting training data: {e}")
            return False
    
    def import_training_data(self, input_path: str) -> bool:
        """Import training data from a file."""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            with open(self.training_data_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Training data imported from {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing training data: {e}")
            return False 

    def save_extraction_experience(self, variable_name: str, context_before: str, context_after: str, 
                                  extracted_value: str, confidence: float, reasoning: str, 
                                  extraction_method: str = "contextual"):
        """Save a detailed extraction experience for learning."""
        try:
            experience = {
                'timestamp': datetime.now().isoformat(),
                'variable_name': variable_name,
                'variable_type': self._classify_variable_type(variable_name),
                'context_before': context_before,
                'context_after': context_after,
                'extracted_value': extracted_value,
                'confidence': confidence,
                'reasoning': reasoning,
                'extraction_method': extraction_method,
                'success': confidence > 0.7
            }
            
            # Load existing experiences
            experiences = []
            if os.path.exists(self.history_file): # Changed from extraction_history_file to history_file
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    experiences = data.get('experiences', []) # Changed from extractions to experiences
            
            # Add new experience
            experiences.append(experience)
            
            # Keep only the last 1000 experiences to avoid file bloat
            if len(experiences) > 1000:
                experiences = experiences[-1000:]
            
            # Save updated experiences
            with open(self.history_file, 'w', encoding='utf-8') as f: # Changed from extraction_history_file to history_file
                json.dump({
                    'version': '2.1',
                    'last_updated': datetime.now().isoformat(),
                    'experiences': experiences
                }, f, indent=2, ensure_ascii=False)
            
            # Update learned patterns based on successful extractions
            if confidence > 0.8:
                self._update_learned_patterns(experience)
            
            logger.info(f"💾 Saved extraction experience: {variable_name} → {extracted_value} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to save extraction experience: {e}")
    
    def _classify_variable_type(self, variable_name: str) -> str:
        """Classify variable type for better learning."""
        name_lower = variable_name.lower()
        
        if 'plan name' in name_lower:
            return 'plan_name'
        elif 'mao name' in name_lower or 'organization' in name_lower:
            return 'organization_name'
        elif 'phone' in name_lower:
            return 'phone_number'
        elif 'tty' in name_lower:
            return 'tty_number'
        elif 'address' in name_lower:
            return 'address'
        elif 'remove terms' in name_lower:
            return 'removal_instruction'
        elif 'insert' in name_lower and ('date' in name_lower or 'day' in name_lower):
            return 'date_time'
        elif 'premium' in name_lower or 'cost' in name_lower:
            return 'financial'
        else:
            return 'general'
    
    def _update_learned_patterns(self, experience: Dict):
        """Update learned patterns based on successful extraction."""
        try:
            variable_type = experience['variable_type']
            
            # Load current patterns
            patterns = self._load_learned_patterns()
            
            # Initialize type-specific patterns if not exist
            if variable_type not in patterns:
                patterns[variable_type] = {
                    'successful_contexts': [],
                    'extraction_patterns': [],
                    'confidence_threshold': 0.7
                }
            
            # Add successful context pattern
            context_pattern = {
                'before_context': experience['context_before'],
                'after_context': experience['context_after'],
                'extracted_value': experience['extracted_value'],
                'confidence': experience['confidence'],
                'method': experience['extraction_method'],
                'timestamp': experience['timestamp']
            }
            
            patterns[variable_type]['successful_contexts'].append(context_pattern)
            
            # Keep only the most successful patterns (top 50)
            patterns[variable_type]['successful_contexts'].sort(
                key=lambda x: x['confidence'], reverse=True
            )
            patterns[variable_type]['successful_contexts'] = patterns[variable_type]['successful_contexts'][:50]
            
            # Create extraction patterns from successful contexts
            self._generate_extraction_patterns(patterns[variable_type], experience)
            
            # Save updated patterns
            self._save_learned_patterns(patterns)
            
        except Exception as e:
            logger.error(f"Failed to update learned patterns: {e}")
    
    def _generate_extraction_patterns(self, type_patterns: Dict, experience: Dict):
        """Generate regex patterns from successful extractions."""
        try:
            before_context = experience['context_before']
            after_context = experience['context_after']
            extracted_value = experience['extracted_value']
            variable_type = experience['variable_type']
            
            # Generate context-based patterns
            if before_context and len(before_context.split()) >= 2:
                # Create a pattern that looks for the before context
                before_words = before_context.split()
                if len(before_words) >= 2:
                    pattern_text = " ".join(before_words[-2:])  # Last 2 words
                    # Escape special regex characters but keep word boundaries
                    escaped_pattern = re.escape(pattern_text)
                    
                    if variable_type == 'plan_name':
                        regex_pattern = rf'{escaped_pattern}\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:PPO|HMO|Group))?)'
                    elif variable_type == 'organization_name':
                        regex_pattern = rf'{escaped_pattern}\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
                    else:
                        regex_pattern = rf'{escaped_pattern}\s*([^,.;!?]+)'
                    
                    # Add pattern if not already exists
                    pattern_obj = {
                        'pattern': regex_pattern,
                        'confidence': experience['confidence'],
                        'context_type': 'before',
                        'example_value': extracted_value,
                        'usage_count': 1
                    }
                    
                    # Check if similar pattern exists
                    existing = False
                    for existing_pattern in type_patterns['extraction_patterns']:
                        if existing_pattern['pattern'] == regex_pattern:
                            existing_pattern['usage_count'] += 1
                            existing_pattern['confidence'] = max(
                                existing_pattern['confidence'], 
                                experience['confidence']
                            )
                            existing = True
                            break
                    
                    if not existing:
                        type_patterns['extraction_patterns'].append(pattern_obj)
            
            # Sort patterns by confidence and usage
            type_patterns['extraction_patterns'].sort(
                key=lambda x: (x['confidence'], x['usage_count']), 
                reverse=True
            )
            
            # Keep top 20 patterns per type
            type_patterns['extraction_patterns'] = type_patterns['extraction_patterns'][:20]
            
        except Exception as e:
            logger.error(f"Failed to generate extraction patterns: {e}")
    
    def _load_learned_patterns(self) -> Dict:
        """Load learned patterns from file."""
        try:
            if os.path.exists(self.patterns_file): # Changed from learned_patterns_file to patterns_file
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('patterns', {})
        except Exception as e:
            logger.error(f"Failed to load learned patterns: {e}")
        
        return {}
    
    def _save_learned_patterns(self, patterns: Dict):
        """Save learned patterns to file."""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f: # Changed from learned_patterns_file to patterns_file
                json.dump({
                    'version': '2.1',
                    'last_updated': datetime.now().isoformat(),
                    'patterns': patterns
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save learned patterns: {e}")
    
    def get_learned_patterns_for_variable(self, variable_name: str) -> Dict:
        """Get learned patterns specific to a variable type."""
        variable_type = self._classify_variable_type(variable_name)
        patterns = self._load_learned_patterns()
        return patterns.get(variable_type, {
            'successful_contexts': [],
            'extraction_patterns': [],
            'confidence_threshold': 0.7
        })
    
    def get_smart_suggestions(self, variable_name: str, context_before: str, context_after: str) -> List[Dict]:
        """Get smart suggestions based on learned patterns."""
        try:
            variable_type = self._classify_variable_type(variable_name)
            patterns = self._load_learned_patterns()
            
            if variable_type not in patterns:
                return []
            
            type_patterns = patterns[variable_type]
            suggestions = []
            
            # Look for similar contexts in successful extractions
            for context in type_patterns['successful_contexts']:
                similarity_score = 0
                
                # Check before context similarity
                if context_before and context['before_context']:
                    before_words = set(context_before.lower().split())
                    stored_before_words = set(context['before_context'].lower().split())
                    if before_words and stored_before_words:
                        similarity_score += len(before_words & stored_before_words) / len(before_words | stored_before_words)
                
                # Check after context similarity  
                if context_after and context['after_context']:
                    after_words = set(context_after.lower().split())
                    stored_after_words = set(context['after_context'].lower().split())
                    if after_words and stored_after_words:
                        similarity_score += len(after_words & stored_after_words) / len(after_words | stored_after_words)
                
                if similarity_score > 0.3:  # 30% similarity threshold
                    suggestions.append({
                        'value': context['extracted_value'],
                        'confidence': context['confidence'] * similarity_score,
                        'reasoning': f"Similar context found (similarity: {similarity_score:.2f})",
                        'method': 'learned_pattern'
                    })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x['confidence'], reverse=True)
            return suggestions[:3]  # Top 3 suggestions
            
        except Exception as e:
            logger.error(f"Failed to get smart suggestions: {e}")
            return [] 