#!/usr/bin/env python3
"""
Lightweight validation script to verify changes without heavy dependencies
"""

import sys
import ast
import yaml


def test_main_py_structure():
    """Verify main.py has correct structure"""
    print("Testing main.py structure...")
    
    with open('main.py', 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Check for required imports
    required_imports = ['argparse', 'sys']
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in required_imports:
                    required_imports.remove(alias.name)
    
    assert len(required_imports) == 0, f"Missing imports: {required_imports}"
    
    # Check DataDownloader is NOT imported
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'src.data_downloader':
                assert False, "DataDownloader should not be imported"
    
    # Check for argparse usage
    assert 'ArgumentParser' in code, "ArgumentParser not found"
    assert '--city' in code, "--city argument not found"
    assert '--radius' in code, "--radius argument not found"
    
    print("✓ main.py structure is correct")
    return True


# Constants
API_KEY_PREFIX_SEARCH_LENGTH = 10  # Characters to search before 'google_api_key' for comment marker


def test_config_yaml():
    """Verify config.yaml has API disabled"""
    print("Testing config.yaml...")
    
    with open('config.yaml', 'r') as f:
        content = f.read()
    
    # Check if google_api_key is present and if so, verify it's commented
    def is_api_key_disabled():
        """Check if API key is absent or commented out"""
        if 'google_api_key' not in content:
            return True  # API key section removed entirely
        
        # Find the line with google_api_key
        api_key_pos = content.find('google_api_key')
        # Check if it's commented (# appears in the characters before it)
        prefix = content[max(0, api_key_pos - API_KEY_PREFIX_SEARCH_LENGTH):api_key_pos]
        return '#' in prefix
    
    assert is_api_key_disabled(), "google_api_key should be removed or commented"
    
    # Should have manual download instructions
    assert 'manually download' in content.lower() or 'manual download' in content.lower(), \
        "Should have manual download instructions"
    
    print("✓ config.yaml has API disabled")
    return True


def test_texture_mapper_structure():
    """Verify texture_mapper.py has cleaning methods"""
    print("Testing texture_mapper.py structure...")
    
    with open('src/texture_mapper.py', 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Find all method names in TextureMapper class
    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'TextureMapper':
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
    
    # Check for required cleaning methods
    required_methods = [
        '_clean_images',
        '_remove_temporary_elements',
        '_detect_reflective_surfaces',
        '_detect_vertical_objects',
        '_detect_motion_blur',
        '_generate_intelligent_colors'
    ]
    
    for method in required_methods:
        assert method in methods, f"Method {method} not found in TextureMapper"
    
    # Check for cv2 usage (image processing)
    assert 'cv2.inpaint' in code, "cv2.inpaint not found for temporary element removal"
    
    print("✓ texture_mapper.py has all cleaning methods")
    return True


def test_test_main_exists():
    """Verify test_main.py exists with comprehensive tests"""
    print("Testing test_main.py exists...")
    
    with open('test_main.py', 'r') as f:
        code = f.read()
    
    # Check for important test functions
    test_functions = [
        'test_command_line_arguments',
        'test_pipeline_initialization_with_params',
        'test_no_api_imports',
        'test_texture_cleaning',
        'test_robustness_empty_inputs'
    ]
    
    for test_func in test_functions:
        assert f"def {test_func}" in code, f"Test function {test_func} not found"
    
    print("✓ test_main.py has comprehensive tests")
    return True


def test_documentation():
    """Check for proper documentation strings"""
    print("Testing documentation...")
    
    with open('main.py', 'r') as f:
        main_code = f.read()
    
    with open('src/texture_mapper.py', 'r') as f:
        texture_code = f.read()
    
    # Check for docstrings
    assert '"""' in main_code, "main.py should have docstrings"
    assert '"""' in texture_code, "texture_mapper.py should have docstrings"
    
    # Check for parameter documentation (simplified logic)
    has_args_doc = 'Args:' in main_code
    has_returns_doc = 'Returns:' in texture_code
    
    assert has_args_doc, "Should document arguments"
    assert has_returns_doc, "Should document returns"
    
    print("✓ Documentation is present")
    return True


def run_validation():
    """Run all validation tests"""
    print("=" * 70)
    print("Running Lightweight Validation Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_main_py_structure,
        test_config_yaml,
        test_texture_mapper_structure,
        test_test_main_exists,
        test_documentation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, True))
            print()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {str(e)}")
            results.append((test.__name__, False))
            print()
        except Exception as e:
            print(f"✗ {test.__name__} error: {str(e)}")
            results.append((test.__name__, False))
            print()
    
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<50} {status}")
    
    print("=" * 70)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
    else:
        print(f"\n⚠️  {total - passed} validation test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
