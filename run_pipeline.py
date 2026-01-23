"""
Complete Pipeline Runner
Executes the full workflow from dataset creation to model training
"""
import os
import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Command: {cmd}")
    print()
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(f"\n SUCCESS ({duration:.1f}s)")
        return True
    else:
        print(f"\n FAILED (exit code: {result.returncode})")
        return False

def main():
    print("="*70)
    print("SENTINEL-LEWS COMPLETE PIPELINE")
    print("="*70)
    
    steps = [
        {
            'cmd': 'python dataset_builder/fix_dates_valid.py',
            'desc': 'STEP 1: Generate Valid Labels',
            'optional': False
        },
        {
            'cmd': 'python dataset_builder/build_training.py',
            'desc': 'STEP 2: Build Training Dataset (~3M rows, 280MB)',
            'optional': False
        },
        {
            'cmd': 'python models/train.py',
            'desc': 'STEP 3: Train Model & Generate Evaluation',
            'optional': False
        },
        {
            'cmd': 'python models/inference.py',
            'desc': 'STEP 4: Test Inference Pipeline',
            'optional': True
        },
        {
            'cmd': 'python test_system.py',
            'desc': 'STEP 5: Run System Tests',
            'optional': True
        }
    ]
    
    results = []
    
    for step in steps:
        success = run_command(step['cmd'], step['desc'])
        results.append((step['desc'], success))
        
        if not success and not step['optional']:
            print(f"\n CRITICAL STEP FAILED. Stopping pipeline.")
            break
    
    # Summary
    print(f"\n{'='*70}")
    print("PIPELINE SUMMARY")
    print(f"{'='*70}")
    
    for desc, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {desc}")
    
    passed = sum(1 for _, s in results if s)
    print(f"\nCompleted: {passed}/{len(results)} steps")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
