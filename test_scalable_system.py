#!/usr/bin/env python3
"""
Test script for the scalable year-over-year update system.
Demonstrates how the knowledge base can be used for quick updates.
"""

import json
import os
from knowledge_base_manager import get_knowledge_manager, learn_variable_interaction
from year_update_utility import YearUpdateUtility, quick_year_update, generate_update_preview

def test_knowledge_base_learning():
    """Test learning functionality."""
    print("🧠 Testing Knowledge Base Learning")
    print("=" * 50)
    
    manager = get_knowledge_manager()
    
    # Learn some variables
    test_variables = [
        ("[insert 2025 plan name]", "Medicare Plus Blue PPO", "2025"),
        ("[insert phone number]", "1-800-123-4567", "2025"),
        ("[insert URL]", "https://member.bcbs.com", "2025"),
        ("[insert TTY number]", "711", "2025"),
        ("[insert customer service number]", "1-800-CUSTOMER", "2025"),
        ("[insert 2025 plan name]", "Medicare Plus Blue PPO", "2026"),
        ("[insert phone number]", "1-800-123-4567", "2026"),
        ("[insert URL]", "https://member.bcbs.com", "2026"),
    ]
    
    for var_name, value, year in test_variables:
        learn_variable_interaction(var_name, "insert", value, year)
        print(f"✅ Learned: {var_name} = {value} ({year})")
    
    # Learn year mapping
    manager.learn_year_mapping("2025", "2026", {
        "insert 2025 plan name": "insert 2026 plan name",
        "insert phone number": "insert phone number",
        "insert URL": "insert URL",
        "insert TTY number": "insert TTY number",
        "insert customer service number": "insert customer service number"
    }, {
        "2025": "2026",
        "Medicare Plus Blue PPO": "Medicare Plus Blue PPO 2026"
    })
    
    print(f"✅ Learned year mapping: 2025 → 2026")
    
    # Save knowledge
    manager.save_knowledge()
    print("💾 Knowledge base saved")
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\n📊 Knowledge Base Statistics:")
    print(f"  Total Variables: {stats['total_variables']}")
    print(f"  Year Mappings: {stats['total_year_mappings']}")
    print(f"  Auto Values: {stats['total_auto_values']}")
    print(f"  Patterns: {stats['total_patterns']}")

def test_auto_value_resolution():
    """Test auto-value resolution."""
    print("\n🎯 Testing Auto-Value Resolution")
    print("=" * 50)
    
    manager = get_knowledge_manager()
    
    # Test cases
    test_cases = [
        "[insert 2025 plan name]",
        "[insert phone number]",
        "[insert URL]",
        "[insert TTY number]",
        "[insert customer service number]",
        "[insert 2026 plan name]",  # Should predict from 2025
        "[insert unknown variable]"
    ]
    
    for var_name in test_cases:
        auto_value = manager.get_auto_value(var_name, "2026")
        if auto_value:
            print(f"✅ {var_name} → {auto_value}")
        else:
            print(f"❌ {var_name} → No auto-value found")

def test_year_prediction():
    """Test year-to-year prediction."""
    print("\n🔄 Testing Year-to-Year Prediction")
    print("=" * 50)
    
    manager = get_knowledge_manager()
    
    # Test predictions
    test_cases = [
        ("[insert 2025 plan name]", "2025", "2026"),
        ("[insert phone number]", "2025", "2026"),
        ("[insert URL]", "2025", "2026"),
        ("[insert TTY number]", "2025", "2026"),
    ]
    
    for var_name, source_year, target_year in test_cases:
        predicted_value = manager.predict_value_for_year(var_name, source_year, target_year)
        if predicted_value:
            print(f"✅ {var_name} ({source_year}→{target_year}) → {predicted_value}")
        else:
            print(f"❌ {var_name} ({source_year}→{target_year}) → No prediction")

def test_year_update_utility():
    """Test the year update utility."""
    print("\n🚀 Testing Year Update Utility")
    print("=" * 50)
    
    utility = YearUpdateUtility()
    
    # Test year transformations
    test_transformations = [
        ("insert 2025 plan name", "2025", "2026"),
        ("insert phone number", "2025", "2026"),
        ("insert URL", "2025", "2026"),
    ]
    
    for content, source_year, target_year in test_transformations:
        transformed = utility._apply_year_transformations(content, source_year, target_year)
        print(f"🔄 {content} → {transformed}")
    
    # Test knowledge statistics
    stats = utility.get_knowledge_statistics()
    print(f"\n📊 Knowledge Statistics:")
    print(f"  Total Variables: {stats['total_variables']}")
    print(f"  Year Mappings: {stats['total_year_mappings']}")
    print(f"  Auto Values: {stats['total_auto_values']}")

def test_export_import():
    """Test export/import functionality."""
    print("\n📤 Testing Export/Import")
    print("=" * 50)
    
    manager = get_knowledge_manager()
    
    # Export year mapping data
    export_data = manager.export_for_year_update("2025", "2026")
    print(f"📤 Exported data:")
    print(f"  Variable Mappings: {len(export_data['variable_mappings'])}")
    print(f"  Value Transformations: {len(export_data['value_transformations'])}")
    print(f"  Auto Values: {len(export_data['auto_values'])}")
    print(f"  Predictions: {len(export_data['predictions'])}")
    
    # Save export data to file
    with open("year_mapping_export.json", "w") as f:
        json.dump(export_data, f, indent=2)
    print("💾 Exported to year_mapping_export.json")

def demonstrate_scalability():
    """Demonstrate the scalability benefits."""
    print("\n📈 Scalability Demonstration")
    print("=" * 50)
    
    manager = get_knowledge_manager()
    
    # Simulate multiple years of learning
    years = ["2023", "2024", "2025", "2026"]
    common_variables = [
        "insert plan name",
        "insert phone number", 
        "insert URL",
        "insert TTY number",
        "insert customer service number"
    ]
    
    print("📚 Learning across multiple years...")
    for year in years:
        for var_base in common_variables:
            var_name = f"[{var_base}]"
            value = f"Value for {year}"
            learn_variable_interaction(var_name, "insert", value, year)
        print(f"✅ Learned {len(common_variables)} variables for {year}")
    
    # Show year coverage
    stats = manager.get_statistics()
    print(f"\n📊 Year Coverage:")
    for year, count in stats['year_coverage'].items():
        print(f"  {year}: {count} variables")
    
    # Demonstrate quick update capability
    print(f"\n🚀 Quick Update Capability:")
    print(f"  Total learned variables: {stats['total_variables']}")
    print(f"  Auto values available: {stats['total_auto_values']}")
    print(f"  Year mappings: {stats['total_year_mappings']}")
    print(f"  Efficiency: {(stats['total_auto_values'] / max(stats['total_variables'], 1) * 100):.1f}% auto-fill rate")

def main():
    """Run all tests."""
    print("🧪 Testing Scalable Year-over-Year Update System")
    print("=" * 60)
    
    # Run tests
    test_knowledge_base_learning()
    test_auto_value_resolution()
    test_year_prediction()
    test_year_update_utility()
    test_export_import()
    demonstrate_scalability()
    
    print("\n✅ All tests completed!")
    print("\n🎯 Key Benefits Demonstrated:")
    print("  • Persistent learning across sessions")
    print("  • Auto-value resolution from knowledge base")
    print("  • Year-to-year prediction capabilities")
    print("  • Export/import for external use")
    print("  • Scalable architecture for multiple years")
    print("  • Quick updates without full wizard runs")

if __name__ == "__main__":
    main()
