#!/usr/bin/env python3
"""
UPass CLI - Zero-knowledge password manager
"""
import sys
import argparse
from commands import UPassSession, VaultCommands
from utils import print_error, print_info

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="UPass - Zero-knowledge password manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  upass create-vault             # Create a new vault
  upass login                    # Login to vault
  upass add                      # Add a new password entry
  upass add -g                   # Add with generated password
  upass gen-add github johndoe   # Generate password and add entry
  upass get github               # Get password for 'github' entry
  upass copy github              # Copy password to clipboard only
  upass totp github              # Copy 2FA code to clipboard
  upass list                     # List all entries
  upass search bank              # Search for entries containing 'bank'
  upass update github            # Update an existing entry
  upass regen github             # Regenerate password for entry
  upass delete old-service       # Delete an entry
  upass generate                 # Generate a random password
  
Custom Server Examples:
  upass --server https://my.server.com create-vault
  upass -s https://localhost:8000 login
        """
    )
    
    # Global server option
    parser.add_argument(
        '--server', '-s',
        help='UPass server URL (default: https://server.upass.ch)',
        default=None
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create vault command
    create_parser = subparsers.add_parser('create-vault', help='Create new vault')
    create_parser.add_argument('vault_name', nargs='?', help='Vault name')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to vault')
    login_parser.add_argument('vault_name', nargs='?', help='Vault name')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add new entry')
    add_parser.add_argument('note', nargs='?', help='Entry note/description')
    add_parser.add_argument('-u', '--username', help='Account username')
    add_parser.add_argument('-p', '--password', help='Password')
    add_parser.add_argument('-g', '--generate', action='store_true', help='Generate password')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get entry')
    get_parser.add_argument('note', help='Entry note/description')
    get_parser.add_argument('--no-copy', action='store_true', help="Don't copy password to clipboard")
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all entries')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search entries')
    search_parser.add_argument('query', help='Search query')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update entry')
    update_parser.add_argument('note', nargs='?', help='Entry note/description')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete entry')
    delete_parser.add_argument('note', nargs='?', help='Entry note/description')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate password')
    generate_parser.add_argument('-l', '--length', type=int, default=16, help='Password length')
    generate_parser.add_argument('--no-special', action='store_true', help='Exclude special characters')
    
    # Generate and add command
    gen_add_parser = subparsers.add_parser('gen-add', help='Generate password and add entry')
    gen_add_parser.add_argument('note', help='Entry note/description')
    gen_add_parser.add_argument('username', help='Account username')
    gen_add_parser.add_argument('-l', '--length', type=int, default=16, help='Password length')
    gen_add_parser.add_argument('--no-special', action='store_true', help='Exclude special characters')
    
    # Copy password only
    copy_parser = subparsers.add_parser('copy', help='Copy password to clipboard')
    copy_parser.add_argument('note', help='Entry note/description')
    
    # Copy TOTP command
    totp_parser = subparsers.add_parser('totp', help='Copy 2FA code to clipboard')
    totp_parser.add_argument('note', help='Entry note/description')
    
    # Regenerate password for existing entry
    regen_parser = subparsers.add_parser('regen', help='Regenerate password for entry')
    regen_parser.add_argument('note', help='Entry note/description')
    regen_parser.add_argument('-l', '--length', type=int, default=16, help='Password length')
    regen_parser.add_argument('--no-special', action='store_true', help='Exclude special characters')
    
    # Quick add with prompts
    quick_parser = subparsers.add_parser('quick', help='Quick add entry with prompts')
    quick_parser.add_argument('note', help='Entry note/description')
    
    # Server management commands
    servers_parser = subparsers.add_parser('servers', help='List configured servers')
    
    # Logout command
    logout_parser = subparsers.add_parser('logout', help='Logout and clear session')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show session status')
    
    return parser

def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create session with custom server if specified
    session = UPassSession(server_url=args.server)
    vault_commands = VaultCommands(session)
    
    try:
        # Handle commands
        if args.command == 'create-vault':
            if session.register(args.vault_name):
                return 0
            return 1
        
        elif args.command == 'login':
            if session.login(args.vault_name):
                return 0
            return 1
        
        elif args.command == 'add':
            # Auto-login if not authenticated
            if not session.authenticated:
                # Don't print message if we have a saved session that might work
                if not session.login():
                    return 1
            
            if vault_commands.add_entry(
                note=args.note,
                username=args.username,
                password=args.password,
                generate=args.generate
            ):
                return 0
            return 1
        
        elif args.command == 'get':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.get_entry(args.note, copy_password=not args.no_copy):
                return 0
            return 1
        
        elif args.command == 'list':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            vault_commands.list_entries()
            return 0
        
        elif args.command == 'search':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            vault_commands.list_entries(search=args.query)
            return 0
        
        elif args.command == 'update':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.update_entry(args.note):
                return 0
            return 1
        
        elif args.command == 'delete':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.delete_entry(args.note):
                return 0
            return 1
        
        elif args.command == 'generate':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.generate_password(args.length, not args.no_special):
                return 0
            return 1
        
        elif args.command == 'gen-add':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.generate_and_add(args.note, args.username, args.length, not args.no_special):
                return 0
            return 1
        
        elif args.command == 'copy':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.copy_password(args.note):
                return 0
            return 1
        
        elif args.command == 'totp':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.copy_totp(args.note):
                return 0
            return 1
        
        elif args.command == 'regen':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.regenerate_password(args.note, args.length, not args.no_special):
                return 0
            return 1
        
        elif args.command == 'quick':
            if not session.authenticated:
                print_info("Please login first")
                if not session.login():
                    return 1
            
            if vault_commands.quick_add(args.note):
                return 0
            return 1
        
        elif args.command == 'servers':
            # List all configured servers
            from utils.config import get_config
            config = get_config()
            servers = config.list_servers()
            
            if not servers:
                print_info("No servers configured yet")
                return 0
            
            print_info("Configured servers:")
            for server in servers:
                current = " (current)" if server['server_url'] == session.config.server_url else ""
                username = f" - {server['last_username']}" if server['last_username'] else ""
                print(f"  {server['server_url']}{username}{current}")
            return 0
        
        elif args.command == 'logout':
            session.logout()
            return 0
        
        elif args.command == 'status':
            if session.authenticated:
                print_info(f"Logged in as: {session.username}")
                print_info(f"Server: {session.config.server_url}")
                print_info(f"Vault entries: {len(session.vault.entries)}")
            else:
                print_info("Not logged in")
                print_info(f"Server: {session.config.server_url}")
            return 0
        
        else:
            print_error(f"Unknown command: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\nAborted")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1
    finally:
        # Only cleanup on explicit logout, not after every command
        pass

if __name__ == '__main__':
    sys.exit(main())