#!/usr/bin/env python3
"""
Knowledge Base Manager for CMS Model Updater
Handles persistent storage and retrieval of learned patterns, values, and classifications
for scalable year-over-year updates without requiring wizard runs.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class VariableKnowledge:
    """Knowledge entry for a variable pattern."""
    normalized_name: str
    original_names: List[str]  # All case variants seen
    variable_type: str
    common_values: Dict[str, int]  # value -> frequency
    confidence_score: float
    last_updated: str
    year_context: Dict[str, Any]  # Year-specific patterns
    classification_metadata: Dict[str, Any]
    auto_populate_rules: Dict[str, Any]

@dataclass
class YearMapping:
    """Year-to-year mapping knowledge."""
    source_year: str
    target_year: str
    variable_mappings: Dict[str, str]  # normalized_name -> normalized_name
    value_transformations: Dict[str, str]  # pattern -> replacement
    confidence_scores: Dict[str, float]

class KnowledgeBaseManager:
    """Manages persistent knowledge for scalable year-over-year updates."""
    
    def __init__(self, base_dir: str = "learning_data"):
        self.base_dir = base_dir
        self.knowledge_file = os.path.join(base_dir, "knowledge_base.json")
        self.year_mappings_file = os.path.join(base_dir, "year_mappings.json")
        self.auto_values_file = os.path.join(base_dir, "auto_values.json")
        self.patterns_file = os.path.join(base_dir, "learned_patterns.json")
        
        # Ensure directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Load existing knowledge
        self.variable_knowledge: Dict[str, VariableKnowledge] = {}
        self.year_mappings: Dict[str, YearMapping] = {}
        self.auto_values: Dict[str, str] = {}
        self.learned_patterns: Dict[str, Any] = {}
        
        self._load_knowledge()
    
    def _load_knowledge(self):
        """Load all knowledge files."""
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.variable_knowledge = {
                        k: VariableKnowledge(**v) for k, v in data.items()
                    }
                logger.info(f"✅ Loaded {len(self.variable_knowledge)} variable knowledge entries")
            
            if os.path.exists(self.year_mappings_file):
                with open(self.year_mappings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.year_mappings = {
                        k: YearMapping(**v) for k, v in data.items()
                    }
                logger.info(f"✅ Loaded {len(self.year_mappings)} year mappings")
            
            if os.path.exists(self.auto_values_file):
                with open(self.auto_values_file, 'r', encoding='utf-8') as f:
                    self.auto_values = json.load(f)
                logger.info(f"✅ Loaded {len(self.auto_values)} auto values")
            
            if os.path.exists(self.patterns_file):
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    self.learned_patterns = json.load(f)
                logger.info(f"✅ Loaded {len(self.learned_patterns)} learned patterns")
                
        except Exception as e:
            logger.error(f"❌ Error loading knowledge base: {e}")
    
    def save_knowledge(self):
        """Save all knowledge to files."""
        try:
            # Save variable knowledge
            knowledge_data = {
                k: asdict(v) for k, v in self.variable_knowledge.items()
            }
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
            
            # Save year mappings
            mappings_data = {
                k: asdict(v) for k, v in self.year_mappings.items()
            }
            with open(self.year_mappings_file, 'w', encoding='utf-8') as f:
                json.dump(mappings_data, f, indent=2, ensure_ascii=False)
            
            # Save auto values
            with open(self.auto_values_file, 'w', encoding='utf-8') as f:
                json.dump(self.auto_values, f, indent=2, ensure_ascii=False)
            
            # Save learned patterns
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_patterns, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Error saving knowledge base: {e}")
    
    def normalize_variable_name(self, var_name: str) -> str:
        """Normalize variable name for consistent lookup."""
        # Remove brackets and normalize
        normalized = re.sub(r'[\[\]]', '', var_name).strip().lower()
        # Remove common prefixes
        normalized = re.sub(r'^(insert|select|add|include)\s+', '', normalized)
        return normalized
    
    def learn_variable(self, var_name: str, var_type: str, value: str, 
                      year: str, classification_metadata: Dict[str, Any] = None):
        """Learn from a variable interaction."""
        normalized_name = self.normalize_variable_name(var_name)
        
        if normalized_name not in self.variable_knowledge:
            # Create new knowledge entry
            self.variable_knowledge[normalized_name] = VariableKnowledge(
                normalized_name=normalized_name,
                original_names=[var_name],
                variable_type=var_type,
                common_values={value: 1},
                confidence_score=0.8,
                last_updated=datetime.now().isoformat(),
                year_context={year: {"value": value, "type": var_type}},
                classification_metadata=classification_metadata or {},
                auto_populate_rules={}
            )
        else:
            # Update existing knowledge
            knowledge = self.variable_knowledge[normalized_name]
            knowledge.original_names.append(var_name)
            knowledge.original_names = list(set(knowledge.original_names))  # Remove duplicates
            
            # Update value frequency
            if value in knowledge.common_values:
                knowledge.common_values[value] += 1
            else:
                knowledge.common_values[value] = 1
            
            # Update year context
            knowledge.year_context[year] = {"value": value, "type": var_type}
            knowledge.last_updated = datetime.now().isoformat()
            
            # Update classification metadata
            if classification_metadata:
                knowledge.classification_metadata.update(classification_metadata)
        
        # Also store as auto value
        self.auto_values[normalized_name] = value
    
    def get_auto_value(self, var_name: str, year: str = None) -> Optional[str]:
        """Get auto-populated value for a variable."""
        normalized_name = self.normalize_variable_name(var_name)
        
        # Check auto values first
        if normalized_name in self.auto_values:
            return self.auto_values[normalized_name]
        
        # Check knowledge base
        if normalized_name in self.variable_knowledge:
            knowledge = self.variable_knowledge[normalized_name]
            
            # If year specified, try year-specific value
            if year and year in knowledge.year_context:
                return knowledge.year_context[year]["value"]
            
            # Return most common value
            if knowledge.common_values:
                return max(knowledge.common_values.items(), key=lambda x: x[1])[0]
        
        return None
    
    def get_variable_knowledge(self, var_name: str) -> Optional[VariableKnowledge]:
        """Get full knowledge for a variable."""
        normalized_name = self.normalize_variable_name(var_name)
        return self.variable_knowledge.get(normalized_name)
    
    def learn_year_mapping(self, source_year: str, target_year: str, 
                          variable_mappings: Dict[str, str], 
                          value_transformations: Dict[str, str]):
        """Learn year-to-year mapping patterns."""
        mapping_key = f"{source_year}_to_{target_year}"
        
        # Calculate confidence scores based on mapping success
        confidence_scores = {}
        for source_var, target_var in variable_mappings.items():
            # Simple confidence based on name similarity
            similarity = self._calculate_name_similarity(source_var, target_var)
            confidence_scores[source_var] = similarity
        
        self.year_mappings[mapping_key] = YearMapping(
            source_year=source_year,
            target_year=target_year,
            variable_mappings=variable_mappings,
            value_transformations=value_transformations,
            confidence_scores=confidence_scores
        )
    
    def get_year_mapping(self, source_year: str, target_year: str) -> Optional[YearMapping]:
        """Get year-to-year mapping."""
        mapping_key = f"{source_year}_to_{target_year}"
        return self.year_mappings.get(mapping_key)
    
    def predict_value_for_year(self, var_name: str, source_year: str, 
                             target_year: str) -> Optional[str]:
        """Predict value for target year based on source year."""
        mapping = self.get_year_mapping(source_year, target_year)
        if not mapping:
            return None
        
        normalized_name = self.normalize_variable_name(var_name)
        
        # Check if this variable has a mapping
        if normalized_name in mapping.variable_mappings:
            mapped_var = mapping.variable_mappings[normalized_name]
            source_value = self.get_auto_value(mapped_var, source_year)
            
            if source_value:
                # Apply value transformations
                transformed_value = self._apply_value_transformations(
                    source_value, mapping.value_transformations
                )
                return transformed_value
        
        return None
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between variable names."""
        # Simple word overlap similarity
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _apply_value_transformations(self, value: str, transformations: Dict[str, str]) -> str:
        """Apply learned value transformations."""
        transformed_value = value
        
        for pattern, replacement in transformations.items():
            if pattern in transformed_value:
                transformed_value = transformed_value.replace(pattern, replacement)
        
        return transformed_value
    
    def get_learned_patterns(self) -> Dict[str, Any]:
        """Get all learned patterns."""
        return self.learned_patterns
    
    def learn_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]):
        """Learn a new pattern."""
        if pattern_type not in self.learned_patterns:
            self.learned_patterns[pattern_type] = []
        
        self.learned_patterns[pattern_type].append({
            **pattern_data,
            "learned_at": datetime.now().isoformat()
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "total_variables": len(self.variable_knowledge),
            "total_year_mappings": len(self.year_mappings),
            "total_auto_values": len(self.auto_values),
            "total_patterns": len(self.learned_patterns),
            "most_common_variables": self._get_most_common_variables(),
            "year_coverage": self._get_year_coverage()
        }
    
    def _get_most_common_variables(self) -> List[Dict[str, Any]]:
        """Get most frequently encountered variables."""
        variables = []
        for normalized_name, knowledge in self.variable_knowledge.items():
            total_occurrences = sum(knowledge.common_values.values())
            variables.append({
                "name": normalized_name,
                "occurrences": total_occurrences,
                "most_common_value": max(knowledge.common_values.items(), key=lambda x: x[1])[0] if knowledge.common_values else None
            })
        
        return sorted(variables, key=lambda x: x["occurrences"], reverse=True)[:10]
    
    def _get_year_coverage(self) -> Dict[str, int]:
        """Get coverage by year."""
        year_counts = {}
        for knowledge in self.variable_knowledge.values():
            for year in knowledge.year_context.keys():
                year_counts[year] = year_counts.get(year, 0) + 1
        return year_counts
    
    def export_for_year_update(self, source_year: str, target_year: str) -> Dict[str, Any]:
        """Export knowledge for year-over-year update."""
        mapping = self.get_year_mapping(source_year, target_year)
        
        export_data = {
            "source_year": source_year,
            "target_year": target_year,
            "variable_mappings": mapping.variable_mappings if mapping else {},
            "value_transformations": mapping.value_transformations if mapping else {},
            "auto_values": {},
            "predictions": {}
        }
        
        # Get auto values for source year
        for normalized_name, knowledge in self.variable_knowledge.items():
            if source_year in knowledge.year_context:
                source_value = knowledge.year_context[source_year]["value"]
                export_data["auto_values"][normalized_name] = source_value
                
                # Predict target year value
                if mapping:
                    predicted_value = self.predict_value_for_year(
                        normalized_name, source_year, target_year
                    )
                    if predicted_value:
                        export_data["predictions"][normalized_name] = predicted_value
        
        return export_data
    
    def import_year_update_data(self, update_data: Dict[str, Any]):
        """Import year update data."""
        source_year = update_data["source_year"]
        target_year = update_data["target_year"]
        
        # Learn year mapping
        self.learn_year_mapping(
            source_year, target_year,
            update_data["variable_mappings"],
            update_data["value_transformations"]
        )
        
        # Learn auto values
        for normalized_name, value in update_data["auto_values"].items():
            self.auto_values[normalized_name] = value
        
        # Learn predictions
        for normalized_name, predicted_value in update_data["predictions"].items():
            self.auto_values[normalized_name] = predicted_value
        
        self.save_knowledge()

# Global knowledge base manager instance
_knowledge_manager = None

def get_knowledge_manager() -> KnowledgeBaseManager:
    """Get or create the global knowledge base manager."""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeBaseManager()
    return _knowledge_manager

def save_knowledge_base():
    """Save the knowledge base."""
    manager = get_knowledge_manager()
    manager.save_knowledge()

def learn_variable_interaction(var_name: str, var_type: str, value: str, 
                             year: str, classification_metadata: Dict[str, Any] = None):
    """Learn from a variable interaction."""
    manager = get_knowledge_manager()
    manager.learn_variable(var_name, var_type, value, year, classification_metadata)

def get_auto_value_for_variable(var_name: str, year: str = None) -> Optional[str]:
    """Get auto-populated value for a variable."""
    manager = get_knowledge_manager()
    return manager.get_auto_value(var_name, year)

def predict_value_for_year(var_name: str, source_year: str, target_year: str) -> Optional[str]:
    """Predict value for target year based on source year."""
    manager = get_knowledge_manager()
    return manager.predict_value_for_year(var_name, source_year, target_year)

# Example usage and testing
if __name__ == "__main__":
    # Test the knowledge base manager
    manager = get_knowledge_manager()
    
    # Learn some variables
    manager.learn_variable("[insert 2025 plan name]", "insert", "Medicare Plus Blue PPO", "2025")
    manager.learn_variable("[insert phone number]", "insert", "1-800-123-4567", "2025")
    manager.learn_variable("[insert URL]", "insert", "https://member.bcbs.com", "2025")
    
    # Learn year mapping
    manager.learn_year_mapping("2025", "2026", {
        "insert 2025 plan name": "insert 2026 plan name",
        "insert phone number": "insert phone number",
        "insert URL": "insert URL"
    }, {
        "2025": "2026",
        "Medicare Plus Blue PPO": "Medicare Plus Blue PPO 2026"
    })
    
    # Test predictions
    predicted_value = manager.predict_value_for_year("[insert 2025 plan name]", "2025", "2026")
    print(f"Predicted value: {predicted_value}")
    
    # Save knowledge
    manager.save_knowledge()
    
    # Print statistics
    stats = manager.get_statistics()
    print(f"Knowledge base statistics: {stats}")
