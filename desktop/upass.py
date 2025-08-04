#!/usr/bin/env python3
"""
UPass - Zero-knowledge password manager
Unified CLI/GUI launcher

Usage:
  ./upass.py                           # Launch GUI
  ./upass.py --server URL              # Launch GUI with custom server
  ./upass.py create-vault              # CLI: Create new vault
  ./upass.py login                     # CLI: Login to vault
  ./upass.py add                       # CLI: Add entry
  ./upass.py get github                # CLI: Get entry
  ./upass.py list                      # CLI: List entries
  ... (all CLI commands)
"""

import sys
import os
import argparse

# Add project root to path
project_root = os.path.dirname(__file__)
cli_path = os.path.join(project_root, 'cli')
gui_path = os.path.join(project_root, 'gui')

def get_cli_commands():
    """Dynamically fetch CLI commands from the CLI module"""
    try:
        # Import CLI using importlib to avoid path conflicts
        import importlib.util
        cli_main_path = os.path.join(cli_path, 'main.py')
        spec = importlib.util.spec_from_file_location("cli_main", cli_main_path)
        cli_main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_main_module)
        
        # Create the parser and extract subcommands
        parser = cli_main_module.create_parser()
        
        # Get all subcommands from the parser
        if hasattr(parser, '_subparsers'):
            subparsers_actions = [
                action for action in parser._actions 
                if isinstance(action, argparse._SubParsersAction)
            ]
            
            if subparsers_actions:
                subparser = subparsers_actions[0]
                return set(subparser.choices.keys())
    except Exception:
        # Fallback to hardcoded list if dynamic fetching fails
        pass
    
    # Fallback: hardcoded commands (backup in case dynamic fetching fails)
    return {
        'create-vault', 'login', 'add', 'get', 'list', 'search', 'update', 
        'delete', 'generate', 'gen-add', 'copy', 'regen', 'quick', 
        'servers', 'logout', 'status'
    }

def is_gui_mode(args):
    """Determine if we should launch GUI or CLI based on actual CLI commands"""
    # Get CLI commands dynamically
    cli_commands = get_cli_commands()
    
    # Filter out global options to find the actual command
    command = None
    i = 0
    while i < len(args):
        arg = args[i]
        
        # Skip global options and their values
        if arg in ['--server', '-s']:
            i += 2  # Skip option and its value
            continue
        elif arg.startswith('--') or arg.startswith('-'):
            i += 1  # Skip other options
            continue
        else:
            # First non-option argument is the command
            command = arg
            break
    
    # If we found a CLI command, use CLI mode
    if command and command in cli_commands:
        return False
    
    # If no CLI command found, use GUI mode
    return True

def launch_gui(server_url=None):
    """Launch the GUI application"""
    try:
        # Import GUI modules
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        
        # Check for required dependencies
        try:
            import nacl.signing
            import nacl.secret
            import nacl.pwhash
            import requests
        except ImportError as e:
            print(f"Missing required dependency: {e}")
            print("Please install required packages:")
            print("pip install pynacl requests pygobject")
            return 1
        
        # Load last used server if no server specified
        if not server_url:
            try:
                # Import config to get last server
                import importlib.util
                config_path = os.path.join(cli_path, 'utils', 'config.py')
                spec = importlib.util.spec_from_file_location("config", config_path)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                
                config = config_module.get_config()
                server_url = config.get_last_server()
            except Exception:
                # Fallback to default if loading config fails
                pass
        
        # Import GUI using importlib to avoid path conflicts
        import importlib.util
        gui_main_path = os.path.join(gui_path, 'main.py')
        spec = importlib.util.spec_from_file_location("gui_main", gui_main_path)
        gui_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gui_main)
        
        # Run GUI application
        app = gui_main.UPassApplication(server_url=server_url)
        return app.run([sys.argv[0]])
        
    except ImportError as e:
        print(f"GUI dependencies not available: {e}")
        print("GUI mode requires GTK3 and PyGObject")
        print("Please install: pip install pygobject")
        return 1
    except Exception as e:
        print(f"Failed to launch GUI: {e}")
        return 1

def launch_cli(args):
    """Launch CLI with the given arguments"""
    try:
        # Add CLI path temporarily for its internal imports
        cli_path_added = False
        if cli_path not in sys.path:
            sys.path.insert(0, cli_path)
            cli_path_added = True
        
        # Import CLI using importlib to avoid path conflicts
        import importlib.util
        cli_main_path = os.path.join(cli_path, 'main.py')
        spec = importlib.util.spec_from_file_location("cli_main", cli_main_path)
        cli_main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_main_module)
        
        # Temporarily replace sys.argv for CLI processing
        original_argv = sys.argv[:]
        sys.argv = [sys.argv[0]] + args
        
        try:
            return cli_main_module.main()
        finally:
            # Restore original argv
            sys.argv = original_argv
            
            # Remove CLI path if we added it
            if cli_path_added and cli_path in sys.path:
                sys.path.remove(cli_path)
            
    except ImportError as e:
        print(f"CLI dependencies not available: {e}")
        return 1
    except Exception as e:
        print(f"Failed to launch CLI: {e}")
        return 1

def parse_server_arg(args):
    """Extract --server argument if present, return (server_url, remaining_args)"""
    server_url = None
    remaining_args = []
    
    i = 0
    while i < len(args):
        if args[i] in ['--server', '-s'] and i + 1 < len(args):
            server_url = args[i + 1]
            i += 2  # Skip both --server and its value
        else:
            remaining_args.append(args[i])
            i += 1
    
    return server_url, remaining_args

def show_help():
    """Show unified help message with dynamic CLI commands"""
    # Import version
    from version import get_version
    
    # Get CLI commands and their descriptions dynamically
    cli_help_lines = []
    try:
        # Import CLI using importlib to avoid path conflicts
        import importlib.util
        cli_main_path = os.path.join(cli_path, 'main.py')
        spec = importlib.util.spec_from_file_location("cli_main", cli_main_path)
        cli_main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_main_module)
        
        parser = cli_main_module.create_parser()
        
        # Extract subparser help
        if hasattr(parser, '_subparsers'):
            subparsers_actions = [
                action for action in parser._actions 
                if isinstance(action, argparse._SubParsersAction)
            ]
            
            if subparsers_actions:
                subparser = subparsers_actions[0]
                for cmd, subp in subparser.choices.items():
                    help_text = subp.description or subp.help or ''
                    cli_help_lines.append(f"    {cmd:<20}        {help_text}")
    except Exception:
        # Fallback to static help if dynamic extraction fails
        cli_help_lines = [
            "    create-vault         Create a new vault",
            "    login               Login to vault", 
            "    add                 Add new entry",
            "    get                 Get entry and copy password",
            "    list                List all entries",
            "    search              Search entries",
            "    update              Update existing entry",
            "    delete              Delete entry",
            "    generate            Generate random password",
            "    gen-add             Generate password and add entry",
            "    copy                Copy password to clipboard only",
            "    regen               Regenerate password for entry",
            "    quick               Quick add with prompts",
            "    servers             List configured servers",
            "    status              Show session status",
            "    logout              Logout and clear session"
        ]
    
    cli_commands_text = '\n'.join(cli_help_lines)
    
    print(f"""UPass v{get_version()} - Zero-knowledge password manager

USAGE:
    upass [OPTIONS]                  Launch GUI
    upass [OPTIONS] <COMMAND> [ARGS] Run CLI command

OPTIONS:
    --server, -s <URL>              UPass server URL (default: https://server.upass.ch)
    --help, -h                      Show this help message

GUI MODE:
    upass                           Launch GUI with default server
    upass --server localhost:8000   Launch GUI with custom server

CLI COMMANDS:
{cli_commands_text}

EXAMPLES:
    upass                           # Launch GUI
    upass --server my.server.com    # Launch GUI with custom server
    upass login                     # CLI: Login to vault
    upass add github                # CLI: Add new entry
    upass get github                # CLI: Get password
    upass --server localhost:8000 login  # CLI: Login to custom server
""")

def main():
    """Main entry point - decide between GUI and CLI mode"""
    # Remove script name from args
    args = sys.argv[1:]
    
    # Handle help requests
    if any(arg in ['--help', '-h', 'help'] for arg in args):
        show_help()
        return 0
    
    # Extract server argument if present
    server_url, remaining_args = parse_server_arg(args)
    
    # Determine mode based on actual commands
    if is_gui_mode(remaining_args):
        # GUI mode
        return launch_gui(server_url)
    else:
        # CLI mode - reconstruct args with server if present
        cli_args = []
        if server_url:
            cli_args.extend(['--server', server_url])
        cli_args.extend(remaining_args)
        
        return launch_cli(cli_args)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)