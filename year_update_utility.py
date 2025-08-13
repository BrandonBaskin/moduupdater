#!/usr/bin/env python3
"""
Year-over-Year Update Utility for CMS Model Updater
Quickly applies learned patterns and mappings to new year documents
without requiring full wizard runs.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any
from docx import Document
from knowledge_base_manager import get_knowledge_manager, predict_value_for_year
from variable_utils import iter_all_paragraphs, iter_all_text_nodes
import logging

logger = logging.getLogger(__name__)

class YearUpdateUtility:
    """Utility for quick year-over-year updates using learned knowledge."""
    
    def __init__(self):
        self.knowledge_manager = get_knowledge_manager()
    
    def quick_update_document(self, source_year: str, target_year: str, 
                            input_docx_path: str, output_docx_path: str) -> Dict[str, Any]:
        """
        Quickly update a document from source year to target year using learned patterns.
        
        Args:
            source_year: Source year (e.g., "2025")
            target_year: Target year (e.g., "2026")
            input_docx_path: Path to input document
            output_docx_path: Path to save updated document
            
        Returns:
            Dictionary with update statistics
        """
        try:
            # Load the document
            doc = Document(input_docx_path)
            
            # Track statistics
            stats = {
                "total_variables": 0,
                "auto_filled": 0,
                "year_transformed": 0,
                "unchanged": 0,
                "errors": 0
            }
            
            # Process all paragraphs (including tables, headers/footers)
            for para in iter_all_paragraphs(doc):
                para_stats = self._process_paragraph(para, source_year, target_year)
                for key in stats:
                    stats[key] += para_stats.get(key, 0)
            
            # Save the updated document
            doc.save(output_docx_path)
            
            logger.info(f"✅ Quick update completed: {stats['auto_filled']} variables auto-filled")
            return {
                "success": True,
                "output_path": output_docx_path,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"❌ Error in quick update: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def apply_answers_to_docx_with_pack(self, model_docx_path: str, out_docx_path: str, pack_json_path: str, answers_json_path: str) -> Dict[str, Any]:
        """Deterministically apply answers using pack occurrences with loc coordinates.

        Primary: write by table/row/cell coordinates when available.
        Secondary: replace placeholders in that cell if present.
        Fallback: if structure shifted, find by normalized left label in the same table.
        """
        try:
            with open(pack_json_path, 'r', encoding='utf-8') as f:
                pack = json.load(f)
            with open(answers_json_path, 'r', encoding='utf-8') as f:
                answrap = json.load(f)
            answers = answrap.get('answers', answrap)

            doc = Document(model_docx_path)
            applied = 0
            missed = []

            def _norm_left(txt: str) -> str:
                t = (txt or '').strip().lower()
                t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
                return re.sub(r"\s+", " ", t).strip()

            # Build per-table left-label index for fallback
            left_index = []
            for ti, tbl in enumerate(doc.tables):
                li = {}
                try:
                    for ri, row in enumerate(tbl.rows):
                        if len(row.cells) >= 2:
                            left = (row.cells[0].text or '').strip()
                            if left:
                                li[_norm_left(left)] = ri
                except Exception:
                    pass
                left_index.append(li)

            for it in pack.get('items', []):
                key = it.get('canonical_key') or it.get('name')
                if key not in answers or not str(answers[key] or '').strip():
                    continue
                value = str(answers[key])
                occs = it.get('occurrences') or []
                wrote_once = False
                for occ in occs:
                    loc = occ.get('loc') or {}
                    t_idx = loc.get('table_idx')
                    r_idx = loc.get('row_idx')
                    c_idx = loc.get('cell_idx', 1)
                    try:
                        if t_idx is not None and r_idx is not None:
                            tbl = doc.tables[t_idx]
                            cell = tbl.rows[r_idx].cells[c_idx]
                            # write value directly
                            cell.text = value
                            # also attempt to clean any placeholder text fragments
                            ph = occ.get('placeholder')
                            if ph and ph in cell.text:
                                cell.text = cell.text.replace(ph, value)
                            wrote_once = True
                            applied += 1
                            break
                    except Exception:
                        # Fallback: attempt lookup by left label in same table
                        try:
                            eff_left = it.get('mbc_effective_label') or it.get('before_context') or ''
                            norm = _norm_left(eff_left)
                            if t_idx is not None and 0 <= t_idx < len(left_index):
                                ri2 = left_index[t_idx].get(norm)
                                if ri2 is not None:
                                    tbl = doc.tables[t_idx]
                                    cell = tbl.rows[ri2].cells[c_idx]
                                    cell.text = value
                                    wrote_once = True
                                    applied += 1
                                    break
                        except Exception:
                            pass
                if not wrote_once:
                    missed.append(key)

            doc.save(out_docx_path)
            return { 'success': True, 'applied': applied, 'missed': missed, 'output_path': out_docx_path }
        except Exception as e:
            return { 'success': False, 'error': str(e) }
    
    def _process_paragraph(self, para, source_year: str, target_year: str) -> Dict[str, int]:
        """Process a paragraph and update variables."""
        stats = {"total_variables": 0, "auto_filled": 0, "year_transformed": 0, "unchanged": 0, "errors": 0}
        
        # Find all variables in the paragraph
        text = para.text
        variable_matches = list(re.finditer(r'\[([^\]]+)\]', text))
        
        if not variable_matches:
            return stats
        
        # Process each variable
        for match in variable_matches:
            stats["total_variables"] += 1
            var_name = match.group(0)  # Full [variable] text
            var_content = match.group(1)  # Content inside brackets
            
            try:
                # Try to get predicted value
                predicted_value = predict_value_for_year(var_name, source_year, target_year)
                
                if predicted_value:
                    # Replace within runs to preserve formatting
                    try:
                        runs = getattr(para, 'runs', [])
                        if runs:
                            for run in runs:
                                if var_name in (run.text or ''):
                                    run.text = (run.text or '').replace(var_name, predicted_value)
                        else:
                            para.text = para.text.replace(var_name, predicted_value)
                    except Exception:
                        para.text = para.text.replace(var_name, predicted_value)
                    stats["auto_filled"] += 1
                    logger.info(f"🎯 Auto-filled: {var_name} → {predicted_value}")
                else:
                    # Try year transformation only
                    transformed_content = self._apply_year_transformations(var_content, source_year, target_year)
                    if transformed_content != var_content:
                        new_var_name = f"[{transformed_content}]"
                        try:
                            runs = getattr(para, 'runs', [])
                            if runs:
                                for run in runs:
                                    if var_name in (run.text or ''):
                                        run.text = (run.text or '').replace(var_name, new_var_name)
                            else:
                                para.text = para.text.replace(var_name, new_var_name)
                        except Exception:
                            para.text = para.text.replace(var_name, new_var_name)
                        stats["year_transformed"] += 1
                        logger.info(f"🔄 Year transformed: {var_name} → {new_var_name}")
                    else:
                        stats["unchanged"] += 1
                        
            except Exception as e:
                logger.error(f"❌ Error processing variable {var_name}: {e}")
                stats["errors"] += 1
        
        return stats
    
    def _apply_year_transformations(self, content: str, source_year: str, target_year: str) -> str:
        """Apply year-specific transformations to variable content."""
        transformed = content
        
        # Replace year references
        transformed = transformed.replace(source_year, target_year)
        
        # Common year patterns
        year_patterns = {
            "twenty twenty five": "twenty twenty six",
            "twenty twenty-five": "twenty twenty-six",
            "2025": "2026",
            "twenty five": "twenty six",
            "twenty-five": "twenty-six"
        }
        
        for old_pattern, new_pattern in year_patterns.items():
            transformed = transformed.replace(old_pattern, new_pattern)
        
        return transformed
    
    def generate_update_report(self, source_year: str, target_year: str, 
                             input_docx_path: str) -> Dict[str, Any]:
        """
        Generate a report of what would be updated without making changes.
        
        Args:
            source_year: Source year
            target_year: Target year
            input_docx_path: Path to input document
            
        Returns:
            Dictionary with update predictions
        """
        try:
            doc = Document(input_docx_path)
            
            report = {
                "source_year": source_year,
                "target_year": target_year,
                "predictions": [],
                "statistics": {
                    "total_variables": 0,
                    "predictable": 0,
                    "unpredictable": 0,
                    "year_only_updates": 0
                }
            }
            
            # Process all paragraphs (including tables, headers/footers)
            for para in iter_all_paragraphs(doc):
                para_predictions = self._analyze_paragraph_predictions(para, source_year, target_year)
                report["predictions"].extend(para_predictions)
                
                for pred in para_predictions:
                    report["statistics"]["total_variables"] += 1
                    if pred["has_prediction"]:
                        report["statistics"]["predictable"] += 1
                    elif pred["year_transformation"]:
                        report["statistics"]["year_only_updates"] += 1
                    else:
                        report["statistics"]["unpredictable"] += 1
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating update report: {e}")
            return {"error": str(e)}
    
    def _analyze_paragraph_predictions(self, para, source_year: str, target_year: str) -> List[Dict[str, Any]]:
        """Analyze what predictions would be made for a paragraph."""
        predictions = []
        
        text = para.text
        variable_matches = list(re.finditer(r'\[([^\]]+)\]', text))
        
        for match in variable_matches:
            var_name = match.group(0)
            var_content = match.group(1)
            
            prediction = {
                "variable": var_name,
                "has_prediction": False,
                "predicted_value": None,
                "year_transformation": False,
                "transformed_variable": None,
                "confidence": 0.0
            }
            
            # Try to get predicted value
            predicted_value = predict_value_for_year(var_name, source_year, target_year)
            if predicted_value:
                prediction["has_prediction"] = True
                prediction["predicted_value"] = predicted_value
                prediction["confidence"] = 0.8  # Could be enhanced with actual confidence scores
            
            # Check year transformation
            transformed_content = self._apply_year_transformations(var_content, source_year, target_year)
            if transformed_content != var_content:
                prediction["year_transformation"] = True
                prediction["transformed_variable"] = f"[{transformed_content}]"
            
            predictions.append(prediction)
        
        return predictions
    
    def export_year_mapping_data(self, source_year: str, target_year: str) -> Dict[str, Any]:
        """Export year mapping data for external use."""
        return self.knowledge_manager.export_for_year_update(source_year, target_year)
    
    def import_year_mapping_data(self, mapping_data: Dict[str, Any]):
        """Import year mapping data from external source."""
        self.knowledge_manager.import_year_update_data(mapping_data)
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        return self.knowledge_manager.get_statistics()

def quick_year_update(source_year: str, target_year: str, 
                    input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Quick year-over-year update function.
    
    Args:
        source_year: Source year (e.g., "2025")
        target_year: Target year (e.g., "2026")
        input_path: Input document path
        output_path: Output document path
        
    Returns:
        Dictionary with results
    """
    utility = YearUpdateUtility()
    return utility.quick_update_document(source_year, target_year, input_path, output_path)

def generate_update_preview(source_year: str, target_year: str, 
                          input_path: str) -> Dict[str, Any]:
    """
    Generate a preview of what would be updated.
    
    Args:
        source_year: Source year
        target_year: Target year
        input_path: Input document path
        
    Returns:
        Dictionary with update preview
    """
    utility = YearUpdateUtility()
    return utility.generate_update_report(source_year, target_year, input_path)

# Example usage and testing
if __name__ == "__main__":
    # Test the year update utility
    utility = YearUpdateUtility()
    
    # Example usage
    print("Year Update Utility Test")
    print("=" * 50)
    
    # Get knowledge statistics
    stats = utility.get_knowledge_statistics()
    print(f"Knowledge Base Statistics:")
    print(f"  Total Variables: {stats['total_variables']}")
    print(f"  Year Mappings: {stats['total_year_mappings']}")
    print(f"  Auto Values: {stats['total_auto_values']}")
    print(f"  Patterns: {stats['total_patterns']}")
    
    # Example year mapping export
    if stats['total_year_mappings'] > 0:
        mapping_data = utility.export_year_mapping_data("2025", "2026")
        print(f"\nYear Mapping Data (2025 → 2026):")
        print(f"  Variable Mappings: {len(mapping_data['variable_mappings'])}")
        print(f"  Value Transformations: {len(mapping_data['value_transformations'])}")
        print(f"  Auto Values: {len(mapping_data['auto_values'])}")
        print(f"  Predictions: {len(mapping_data['predictions'])}")
