# Quick Start Guide

## Summary of Files Created

Here are ALL the files that have been created or modified for this project:

### Documentation Files
1. **understanding.md** - Comprehensive code structure guide with PlantUML diagrams
2. **QUICKSTART.md** - This file - quick reference guide

### Automation Scripts
3. **setup.ps1** - PowerShell automation script
4. **setup.bat** - Windows batch file wrapper

### Test Files (in tests/ directory)
5. **tests/test_database.py** - Database interaction tests
6. **tests/test_streamlit_app.py** - Application logic tests
7. **tests/test_simple.py** - Basic structural tests
8. **tests/conftest.py** - Pytest configuration (already existed, modified)

---

## For Windows Users

### Option 1: Using PowerShell (Recommended)

1. **Open PowerShell** in the project directory:
   ```powershell
   cd c:\Workspace\DevOpsTraining\Snowflake-Cortex-Agent-Learning\cortex-agent-api-demo
   ```

2. **First Time Setup**:
   ```powershell
   .\setup.ps1 -Install
   ```
   This will:
   - Create a virtual environment at `.\venv`
   - Install all dependencies from requirements.txt and requirements-dev.txt
   - Check for required files

3. **Configure Snowflake Credentials** (if not already done):
   - Create directory: `.streamlit`
   - Create file: `.streamlit\secrets.toml`
   - Add your Snowflake credentials (see understanding.md)

4. **Run Tests** (verify everything works):
   ```powershell
   .\setup.ps1 -Test
   ```
   Expected: All 14 tests should pass ✅

5. **Run the Application**:
   ```powershell
   .\setup.ps1 -Run
   ```
   The app will open in your browser at http://localhost:8501

6. **Clean Up** (when needed):
   ```powershell
   .\setup.ps1 -Clean
   ```

### Option 2: Using Command Prompt

1. **Open Command Prompt** in the project directory

2. **First Time Setup**:
   ```cmd
   setup.bat install
   ```

3. **Configure Snowflake Credentials** (same as above)

4. **Run the Application**:
   ```cmd
   setup.bat run
   ```

5. **Run Tests**:
   ```cmd
   setup.bat test
   ```

## Script Commands Reference

### PowerShell (setup.ps1)

```powershell
# Install dependencies
.\setup.ps1 -Install

# Run application
.\setup.ps1 -Run

# Run tests
.\setup.ps1 -Test

# Clean environment
.\setup.ps1 -Clean

# Show help
.\setup.ps1 -Help

# Combine commands
.\setup.ps1 -Install -Run
```

### Batch (setup.bat)

```cmd
# Install dependencies
setup.bat install

# Run application
setup.bat run

# Run tests
setup.bat test

# Clean environment
setup.bat clean

# Show help
setup.bat help
```

## Manual Setup (If Scripts Don't Work)

1. **Create Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Run Application**:
   ```powershell
   streamlit run streamlit.py
   ```

## Troubleshooting

### PowerShell Execution Policy Error

If you get an error about execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

- Ensure Python is installed: [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation
- Restart your terminal after installation

### Snowflake Connection Error

- Verify credentials in `.streamlit\secrets.toml`
- Check Snowflake account is active
- Ensure `setup.sql` was run completely in Snowflake

### Port Already in Use

Run on a different port:
```powershell
streamlit run streamlit.py --server.port 8502
```

## Next Steps

1. Read the full **understanding.md** for detailed code architecture
2. Try example queries in the application
3. Explore the code structure
4. Add your own features

## Sample Queries to Try

Once the app is running, try these:

1. `What was the total sales volume last year?`
2. `Summarize the call with TechCorp Inc`
3. `Which sales rep had the highest deal value?`
4. `Show me all pending deals`
5. `What is the average deal size for the Premium Security product line?`

## Getting Help

- Check **understanding.md** for detailed documentation
- Review error messages in the terminal
- Ensure all setup steps were completed
- Verify Snowflake database is properly configured

## File Locations Summary

```
cortex-agent-api-demo/
├── setup.ps1                    # PowerShell automation script
├── setup.bat                    # Batch file wrapper
├── understanding.md             # Comprehensive documentation
├── QUICKSTART.md               # This file
├── streamlit.py                # Main application
├── setup.sql                   # Database setup script
├── sales_metrics_model.yaml    # Semantic model
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pytest.ini                  # Pytest configuration
├── .streamlit/
│   └── secrets.toml            # Snowflake credentials (create this)
└── tests/
    ├── conftest.py             # Pytest configuration
    ├── test_database.py        # Database tests
    ├── test_streamlit_app.py   # Application tests
    └── test_simple.py          # Basic structural tests
```

---

**That's it! You now have everything you need to get started.**

For detailed explanations, architecture diagrams, and development guidelines, see **understanding.md**.
