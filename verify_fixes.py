"""
Comprehensive verification script for all fixes and improvements.
Runs diagnostic checks on all modules and reports status.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_check(status, message):
    """Print a check result."""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {message}")

def check_imports():
    """Check all critical imports."""
    print_header("CHECKING IMPORTS")
    
    checks = {
        'PIL': 'from PIL import Image',
        'numpy': 'import numpy as np',
        'streamlit': 'import streamlit as st',
        'google.generativeai': 'import google.generativeai as genai',
        'sklearn': 'from sklearn.ensemble import RandomForestClassifier',
        'pickle': 'import pickle',
        'json': 'import json'
    }
    
    all_ok = True
    for module_name, import_stmt in checks.items():
        try:
            exec(import_stmt)
            print_check(True, f"{module_name}")
        except ImportError:
            print_check(False, f"{module_name}")
            all_ok = False
    
    return all_ok

def check_modules():
    """Check all project modules."""
    print_header("CHECKING PROJECT MODULES")
    
    modules = {
        'verify.py': 'verify',
        'logger_config.py': 'logger_config',
        'validators.py': 'validators',
        'exceptions.py': 'exceptions',
        'rate_limiter.py': 'rate_limiter',
        'retry_utils.py': 'retry_utils',
        'security.py': 'security',
        'gemini_card_detector.py': 'gemini_card_detector',
        'trained_model_predictor.py': 'trained_model_predictor',
        'train_card_detector.py': 'train_card_detector'
    }
    
    all_ok = True
    for filename, module_name in modules.items():
        try:
            __import__(module_name)
            print_check(True, f"{filename}")
        except Exception as e:
            print_check(False, f"{filename}: {str(e)[:50]}")
            all_ok = False
    
    return all_ok

def check_api_methods():
    """Check that API methods exist and have correct signatures."""
    print_header("CHECKING API METHOD SIGNATURES")
    
    try:
        from rate_limiter import APIUsageTracker, QuotaEnforcer
        tracker = APIUsageTracker()
        enforcer = QuotaEnforcer(tracker)
        
        checks = [
            ('record_api_call', callable(tracker.record_api_call)),
            ('get_user_cost', callable(tracker.get_user_cost)),
            ('get_user_stats', callable(tracker.get_user_stats)),
            ('check_quota', callable(tracker.check_quota)),
            ('check_quota_before_call', callable(enforcer.check_quota_before_call)),
        ]
        
        all_ok = True
        for method_name, exists in checks:
            print_check(exists, f"APIUsageTracker.{method_name}")
            if not exists:
                all_ok = False
        
        return all_ok
    except Exception as e:
        print_check(False, f"Error loading rate limiter: {e}")
        return False

def check_trained_models():
    """Check if trained models are available and loaded."""
    print_header("CHECKING TRAINED MODELS")
    
    try:
        from trained_model_predictor import get_model_info, is_model_ready
        
        info = get_model_info()
        ready = is_model_ready()
        
        print_check(ready, "Models loaded and ready")
        
        if ready and 'training_stats' in info:
            stats = info['training_stats']
            print(f"\n  Training Statistics:")
            print(f"    • Accuracy: {stats['accuracy']:.2%}")
            print(f"    • Total Samples: {stats['total_samples']}")
            print(f"    • Samples per class:")
            for card_type, count in stats['samples_per_class'].items():
                print(f"      - {card_type}: {count}")
        
        return ready
    except Exception as e:
        print_check(False, f"Error checking models: {e}")
        return False

def check_gemini_detector():
    """Check gemini_card_detector fixes."""
    print_header("CHECKING GEMINI DETECTOR FIXES")
    
    try:
        from gemini_card_detector import detect_card_type, extract_card_text, configure_gemini
        
        # Check functions exist
        checks = [
            ('configure_gemini', callable(configure_gemini)),
            ('detect_card_type', callable(detect_card_type)),
            ('extract_card_text', callable(extract_card_text)),
        ]
        
        all_ok = True
        for func_name, exists in checks:
            print_check(exists, f"Function: {func_name}")
            if not exists:
                all_ok = False
        
        return all_ok
    except Exception as e:
        print_check(False, f"Error loading gemini_card_detector: {e}")
        return False

def check_files():
    """Check if all important files exist."""
    print_header("CHECKING FILE STRUCTURE")
    
    required_files = [
        'app_gemini.py',
        'gemini_card_detector.py',
        'rate_limiter.py',
        'trained_model_predictor.py',
        'train_card_detector.py',
        'models/card_type_detector.pkl',
        'models/label_encoder.pkl',
        'models/field_patterns.json',
        'training_data/GHANA CARDS',
        'training_data/passport photos'
    ]
    
    all_ok = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        print_check(exists, file_path)
        if not exists:
            all_ok = False
    
    return all_ok

def check_api_integration():
    """Test actual API integration."""
    print_header("TESTING API INTEGRATION")
    
    try:
        from rate_limiter import APIUsageTracker
        
        # Test recording an API call
        tracker = APIUsageTracker()
        cost = tracker.record_api_call('test_user', 'gemini-1.5-flash', 1000, 500)
        print_check(cost > 0, f"API call tracking: ${cost:.6f}")
        
        # Test quota check
        within_quota, info = tracker.check_quota('test_user', max_cost=10.0)
        print_check(within_quota, f"Quota check: {within_quota} (Cost: ${info['current_cost']:.6f})")
        
        # Test user stats
        stats = tracker.get_user_stats('test_user')
        print_check('calls' in stats, f"User stats: {stats['calls']} calls recorded")
        
        return True
    except Exception as e:
        print_check(False, f"API integration test: {e}")
        return False

def generate_summary():
    """Generate a summary report."""
    print_header("VERIFICATION SUMMARY")
    
    all_checks = {
        'Imports': check_imports(),
        'Modules': check_modules(),
        'API Methods': check_api_methods(),
        'Trained Models': check_trained_models(),
        'Gemini Detector': check_gemini_detector(),
        'File Structure': check_files(),
        'API Integration': check_api_integration(),
    }
    
    print("\n" + "="*70)
    print(f"  VERIFICATION RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    for check_name, result in all_checks.items():
        status_text = "✓ PASS" if result else "✗ FAIL"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status_text}{reset} - {check_name}")
    
    overall = all(all_checks.values())
    print("\n" + "-"*70)
    
    if overall:
        print("\033[92m✓ ALL CHECKS PASSED - System ready for use!\033[0m")
    else:
        print("\033[91m✗ Some checks failed - see above for details\033[0m")
    
    print("-"*70 + "\n")
    
    return overall, all_checks

def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "ID VERIFICATION SYSTEM VERIFICATION" + " "*19 + "║")
    print("║" + " "*20 + "Comprehensive Diagnostic Check" + " "*18 + "║")
    print("╚" + "="*68 + "╝")
    
    overall, results = generate_summary()
    
    # Generate detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'PASS' if overall else 'FAIL',
        'checks': {k: v for k, v in results.items()},
        'summary': {
            'total_checks': len(results),
            'passed': sum(results.values()),
            'failed': len(results) - sum(results.values())
        }
    }
    
    # Save report
    report_path = Path('verification_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📊 Detailed report saved to: {report_path}")
    
    return 0 if overall else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
