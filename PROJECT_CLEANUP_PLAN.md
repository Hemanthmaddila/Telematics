# Project Cleanup Plan

This document outlines what will be removed from the Telematics project to make it more streamlined for cloud deployment.

## Directories to Remove

1. **venv** - Virtual environment directory (should not be in repository)
2. **examples** - Empty directory
3. **k8s** - Empty directory
4. **notebooks** - Empty directory
5. **demo** - Unnecessary demo files
6. **testing** - Likely duplicate of tests directory

## Files to Remove

1. **cleanup_unnecessary_files.bat** - Self-referential cleanup script
2. **restart_with_new_ports.bat** - Windows-specific script
3. **start_clean_system.bat** - Windows-specific script
4. **test_complete_system.py** - Duplicate testing
5. **test_everything_simple.py** - Duplicate testing
6. **test_mlflow.bat** - Windows-specific test script
7. **mlflow_simple.yaml** - Simplified config
8. **MICROSERVICES_QUICK_START.md** - Redundant with main README
9. **README_REAL.md** - Duplicate README

## Directories to Consolidate

1. **automation** - May be redundant with deployment directory
2. **init-scripts** - May be redundant
3. **mlops** - May be redundant with existing ML functionality

## Files to Keep (Essential)

1. **src/telematics_ml** - Core source code
2. **microservices** - Service implementations
3. **api-gateway** - API gateway implementation
4. **scripts** - Deployment and pipeline scripts
5. **config** - Configuration files
6. **data** - Data schemas and processing
7. **models** - ML models
8. **requirements.txt** - Dependencies
9. **README.md** - Main documentation
10. **tutorials** - New tutorial files we're creating

## Implementation Steps

1. Remove unnecessary directories and files
2. Consolidate redundant functionality
3. Organize remaining files into a cleaner structure
4. Update documentation to reflect new structure