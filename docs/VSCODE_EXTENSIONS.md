# VS Code Extensions for Raspberry Pi Thermostat Project

## Essential Extensions (Enable These)

### Python Development
1. **Python** (`ms-python.python`)
   - Core Python language support
   - IntelliSense, debugging, code navigation
   - **Required**

2. **Pylance** (`ms-python.vscode-pylance`)
   - Fast Python language server
   - Type checking and auto-completion
   - **Required**

3. **Python Debugger** (`ms-python.debugpy`)
   - Debugging support for Python
   - **Required**

### Remote Development
4. **Remote - SSH** (`ms-vscode-remote.remote-ssh`)
   - Edit files directly on Raspberry Pi
   - Run/debug code on the Pi
   - **Highly Recommended** - Essential for working on the Pi

### Configuration Files
5. **YAML** (`redhat.vscode-yaml`)
   - systemd service file editing
   - Future config file support
   - **Optional but helpful**

6. **EditorConfig** (`EditorConfig.EditorConfig`)
   - Maintain consistent coding styles
   - **Optional**

## Optional Extensions (Consider These)

### Code Quality
- **Flake8** or **Black Formatter** (for Python linting/formatting)
  - Already configured in settings.json
  - Install via: `pip install flake8 black` in venv

### Documentation
- **Markdown All in One** (`yzhang.markdown-all-in-one`)
  - Better markdown editing for README files
  - Table of contents generation

### Git Integration
- **GitLens** (`eamodio.gitlens`)
  - Enhanced git features (history, blame, etc.)
  - Only if you want advanced Git features

### Hardware Documentation
- **ASCII Tree Generator** (for wiring diagrams)
  - If you want to create more ASCII art diagrams

## Extensions to DISABLE/Uninstall

Based on this project's needs, you can safely disable:

### Web Development
- ❌ ESLint
- ❌ Prettier
- ❌ HTML/CSS/JavaScript extensions
- ❌ React/Vue/Angular extensions
- ❌ Live Server
- ❌ REST Client

### Cloud/Containers (Offline Project)
- ❌ Azure Account
- ❌ Azure Functions
- ❌ Azure Tools
- ❌ Docker
- ❌ Kubernetes

### Other Languages
- ❌ C/C++ (unless you plan to add C extensions)
- ❌ C# / .NET
- ❌ Java
- ❌ Go
- ❌ Rust
- ❌ PHP
- ❌ Ruby

### Databases (Not Used)
- ❌ SQL Server
- ❌ MongoDB
- ❌ PostgreSQL
- ❌ MySQL

### Other
- ❌ Jupyter (not using notebooks for this)
- ❌ PowerShell (wrong platform - this is Python on Linux)

## How to Manage Extensions

### Install Recommended Extensions
When you open this project in VS Code, you'll see a notification:
"This workspace has extension recommendations"
- Click **Install All**

Or manually:
1. Open Extensions view (Ctrl+Shift+X)
2. Type `@recommended`
3. Install the recommended extensions

### Disable Unnecessary Extensions
1. Open Extensions view (Ctrl+Shift+X)
2. Find extension to disable
3. Click gear icon → **Disable (Workspace)**
   - This disables only for this project
   - Extension remains enabled for other projects

### Uninstall Unused Extensions
If you never use an extension:
1. Open Extensions view
2. Find extension
3. Click **Uninstall**

## Remote SSH Setup

To work on the Raspberry Pi directly:

1. Install Remote - SSH extension
2. Press F1 → "Remote-SSH: Connect to Host"
3. Enter: `pi@thermostat.local`
4. Enter password
5. VS Code will connect and install server components on Pi
6. Open folder: `/home/pi/thermostat`

Now you can:
- Edit files directly on the Pi
- Run/debug Python code on actual hardware
- Access Pi terminal from VS Code

## Settings Applied

The `.vscode/settings.json` file includes:
- Python virtual environment configuration
- Flake8 linting enabled
- Black formatting on save
- 88-character ruler (PEP 8 compatible)
- Python-specific formatting rules
- File associations for .env files

## Performance Tips

### For Slower Computers
- Disable GitLens (can be resource-heavy)
- Disable Pylance type checking: Set `"python.analysis.typeCheckingMode": "off"`
- Close unused editor groups

### For Remote Development
- Install extensions on SSH remote (not locally)
- Use "Install on SSH" button when prompted
- Some extensions work better remotely (Python, debugger)

## Minimal Setup (Bare Bones)

If you want absolute minimum:
1. Python extension
2. Remote - SSH extension
3. Nothing else

Edit on Pi, test on Pi, done.

## Full-Featured Setup (Recommended)

For best experience:
1. All "Essential" extensions above
2. Flake8 + Black for code quality
3. Markdown All in One for documentation
4. GitLens if you use Git heavily

## Extension Installation Commands

If you prefer CLI installation:

```bash
# Essential
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.debugpy
code --install-extension ms-vscode-remote.remote-ssh

# Optional
code --install-extension redhat.vscode-yaml
code --install-extension EditorConfig.EditorConfig
code --install-extension yzhang.markdown-all-in-one
```

## Verification

After setup, verify:
1. Python extension shows correct interpreter (venv)
2. Remote SSH can connect to Pi
3. No extension errors in Output panel
4. IntelliSense works in Python files

Check: Open `src/thermostat.py` and hover over `GPIO` - should show documentation.
