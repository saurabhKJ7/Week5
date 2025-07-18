#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly
"""

import sys
import traceback

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing Excel Sheets Agent imports...")
    
    try:
        # Test basic imports
        import pandas as pd
        print("✅ pandas imported successfully")
        
        import numpy as np
        print("✅ numpy imported successfully")
        
        # Test Excel Agent imports
        from excel_agent.main import ExcelAgent
        print("✅ ExcelAgent imported successfully")
        
        from excel_agent.utils.config import Config
        print("✅ Config imported successfully")
        
        from excel_agent.utils.column_mapper import ColumnMapper
        print("✅ ColumnMapper imported successfully")
        
        from excel_agent.utils.chunking import DataChunker
        print("✅ DataChunker imported successfully")
        
        # Test LangChain imports (optional)
        try:
            from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
            print("✅ LangChain pandas agent imported successfully")
        except ImportError as e:
            print(f"⚠️  LangChain pandas agent import failed: {e}")
        
        # Test configuration
        config = Config()
        print("✅ Config object created successfully")
        
        # Test column mapper
        mapper = ColumnMapper()
        print("✅ ColumnMapper object created successfully")
        
        # Test chunker
        chunker = DataChunker()
        print("✅ DataChunker object created successfully")
        
        print("\n🎉 All core imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        print(f"📍 Error details: {traceback.format_exc()}")
        return False

def test_sample_data():
    """Test sample data loading"""
    print("\n📊 Testing sample data loading...")
    
    try:
        import pandas as pd
        from pathlib import Path
        
        # Check if sample data exists
        sample_files = [
            "sample_data/comprehensive_data.xlsx",
            "sample_data/sales_data.xlsx",
            "sample_data/customer_data.xlsx"
        ]
        
        for file_path in sample_files:
            if Path(file_path).exists():
                df = pd.read_excel(file_path)
                print(f"✅ {file_path}: {len(df)} rows, {len(df.columns)} columns")
            else:
                print(f"⚠️  {file_path} not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample data error: {e}")
        return False

def test_agent_creation():
    """Test agent creation with sample data"""
    print("\n🤖 Testing agent creation...")
    
    try:
        from excel_agent.main import ExcelAgent
        from excel_agent.utils.config import Config
        from pathlib import Path
        
        # Check if we have sample data
        sample_file = "sample_data/sales_data.xlsx"
        if not Path(sample_file).exists():
            print(f"⚠️  Sample file {sample_file} not found, skipping agent test")
            return True
        
        # Create config
        config = Config()
        
        # Create agent
        agent = ExcelAgent(config, sample_file)
        print("✅ ExcelAgent created successfully")
        
        # Test file info
        info = agent.get_file_info()
        print(f"✅ File info: {info['worksheet_count']} worksheets, {info['total_rows']} rows")
        
        # Test preview
        preview = agent.get_preview()
        print(f"✅ Preview: {len(preview)} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        print(f"📍 Error details: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("🚀 Excel Sheets Agent - Import Test")
    print("=" * 50)
    
    tests = [
        ("Core Imports", test_imports),
        ("Sample Data", test_sample_data),
        ("Agent Creation", test_agent_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed! The Excel Sheets Agent is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Set your API key in the .env file")
        print("2. Run: streamlit run app.py")
        print("3. Open: http://localhost:8501")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 