import pyperclip
from utils import (
    get_input, get_password, confirm_action, print_error, 
    print_success, print_info, format_table, format_datetime, format_date
)

class VaultCommands:
    """Vault management commands"""
    
    def __init__(self, session):
        self.session = session
    
    def add_entry(self, note: str = None, username: str = None, password: str = None, generate: bool = False):
        """Add a new entry to the vault"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        # Get note
        if not note:
            note = get_input("Title: ")
            if not note:
                return False
        
        # Get account username
        if not username:
            username = get_input("Account username: ")
            if not username:
                return False
        
        # Get or generate password
        if generate:
            length = 16
            length_input = get_input("Password length (16): ", required=False)
            if length_input and length_input.isdigit():
                length = int(length_input)
            
            special = get_input("Include special characters? (Y/n): ", required=False)
            include_special = special.lower() != 'n'
            
            password = self.session.crypto.generate_password(length, include_special)
            print_info(f"Generated password: {password}")
            
            # Copy to clipboard if available
            try:
                pyperclip.copy(password)
                print_info("Password copied to clipboard")
            except:
                pass
        elif not password:
            password = get_password("Password: ")
        
        # Add to vault
        try:
            self.session.vault.add_entry(username, password, note)
            if self.session.save_vault():
                print_success(f"Added entry '{note}'")
                return True
        except ValueError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Failed to add entry: {e}")
        
        return False
    
    def get_entry(self, note: str = None, copy_password: bool = True):
        """Get an entry from the vault"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        if not note:
            note = get_input("Title: ")
            if not note:
                return False
        
        entry = self.session.vault.get_entry(note)
        if not entry:
            print_error(f"Entry '{note}' not found")
            return False
        
        print_info(f"Title: {entry.note}")
        print_info(f"Account: {entry.username}")
        print_info(f"Password: {entry.password}")
        print_info(f"Created: {format_datetime(entry.created_at)}")
        print_info(f"Updated: {format_datetime(entry.updated_at)}")
        
        # Copy password to clipboard
        if copy_password:
            try:
                pyperclip.copy(entry.password)
                print_success("Password copied to clipboard")
            except:
                print_info("Could not copy to clipboard")
        
        return True
    
    def generate_and_add(self, note: str, username: str, length: int = 16, special_chars: bool = True, readable: bool = False, words: bool = False):
        """Generate password and add entry in one command"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        try:
            # Generate password
            if readable or words:
                password = self.session.crypto.generate_readable_password(length, words)
            else:
                password = self.session.crypto.generate_password(length, special_chars)
            print_info(f"Generated password: {password}")
            
            # Add to vault
            self.session.vault.add_entry(username, password, note)
            if self.session.save_vault():
                print_success(f"Added entry '{note}' with generated password")
                
                # Copy to clipboard
                try:
                    pyperclip.copy(password)
                    print_info("Password copied to clipboard")
                except:
                    pass
                
                return True
        except ValueError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Failed to add entry: {e}")
        
        return False
    
    def copy_password(self, note: str):
        """Copy password to clipboard without displaying it"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        entry = self.session.vault.get_entry(note)
        if not entry:
            print_error(f"Entry '{note}' not found")
            return False
        
        try:
            pyperclip.copy(entry.password)
            print_success(f"Password for '{note}' copied to clipboard")
            return True
        except:
            print_error("Could not copy to clipboard")
            return False
    
    def regenerate_password(self, note: str, length: int = 16, special_chars: bool = True, readable: bool = False, words: bool = False):
        """Regenerate password for an existing entry"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        entry = self.session.vault.get_entry(note)
        if not entry:
            print_error(f"Entry '{note}' not found")
            return False
        
        # Confirm regeneration
        if not confirm_action(f"Regenerate password for '{note}'?"):
            print_info("Cancelled")
            return False
        
        try:
            # Generate new password
            if readable or words:
                new_password = self.session.crypto.generate_readable_password(length, words)
            else:
                new_password = self.session.crypto.generate_password(length, special_chars)
            print_info(f"New password: {new_password}")
            
            # Update entry
            self.session.vault.update_entry(note, password=new_password)
            
            if self.session.save_vault():
                print_success(f"Regenerated password for '{note}'")
                
                # Copy to clipboard
                try:
                    pyperclip.copy(new_password)
                    print_info("New password copied to clipboard")
                except:
                    pass
                
                return True
                
        except ValueError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Failed to regenerate password: {e}")
        
        return False
    
    def quick_add(self, note: str):
        """Quick add with minimal prompts"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        print_info(f"Quick add for '{note}'")
        
        # Get account username
        username = get_input("Account username: ")
        if not username:
            return False
        
        # Ask for password option
        print_info("Password options:")
        print_info("1. Generate strong password (recommended)")
        print_info("2. Enter custom password")
        
        choice = get_input("Choose option (1): ", required=False)
        if not choice:
            choice = "1"
        
        if choice == "1":
            # Generate password
            length = 16
            length_input = get_input("Password length (16): ", required=False)
            if length_input and length_input.isdigit():
                length = int(length_input)
            
            special = get_input("Include special characters? (Y/n): ", required=False)
            include_special = special.lower() != 'n'
            
            password = self.session.crypto.generate_password(length, include_special)
            print_info(f"Generated password: {password}")
            
        elif choice == "2":
            # Custom password
            password = get_password("Password: ")
        else:
            print_error("Invalid option")
            return False
        
        # Add to vault
        try:
            self.session.vault.add_entry(username, password, note)
            if self.session.save_vault():
                print_success(f"Added entry '{note}'")
                
                # Copy to clipboard
                try:
                    pyperclip.copy(password)
                    print_info("Password copied to clipboard")
                except:
                    pass
                
                return True
        except ValueError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Failed to add entry: {e}")
        
        return False
    
    def list_entries(self, search: str = None):
        """List all entries in the vault"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        if search:
            entries = self.session.vault.search_entries(search)
            print_info(f"Search results for '{search}':")
        else:
            entries = self.session.vault.list_entries()
        
        if not entries:
            print_info("No entries found")
            return False
        
        # Format as table
        headers = ["Title", "Account", "Created"]
        rows = []
        for entry in entries:
            created = format_date(entry["created_at"])
            rows.append([entry["note"], entry["username"], created])
        
        print(format_table(headers, rows))
        print_info(f"Total: {len(entries)} entries")
        return True
    
    def update_entry(self, note: str = None):
        """Update an existing entry"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        if not note:
            note = get_input("Title to update: ")
            if not note:
                return False
        
        entry = self.session.vault.get_entry(note)
        if not entry:
            print_error(f"Entry '{note}' not found")
            return False
        
        print_info(f"Updating entry '{note}'")
        print_info(f"Current username: {entry.username}")
        print_info("Leave empty to keep current values")
        
        # Get new values
        new_username = get_input(f"New username ({entry.username}): ", required=False)
        new_password = None
        
        password_choice = get_input("Update password? (y/N): ", required=False)
        if password_choice.lower() == 'y':
            generate = get_input("Generate new password? (y/N): ", required=False)
            if generate.lower() == 'y':
                length = 16
                length_input = get_input("Password length (16): ", required=False)
                if length_input and length_input.isdigit():
                    length = int(length_input)
                
                special = get_input("Include special characters? (Y/n): ", required=False)
                include_special = special.lower() != 'n'
                
                new_password = self.session.crypto.generate_password(length, include_special)
                print_info(f"Generated password: {new_password}")
            else:
                new_password = get_password("New password: ")
        
        new_note = get_input(f"New title ({entry.note}): ", required=False)
        
        # Update entry
        try:
            self.session.vault.update_entry(
                note,
                username=new_username if new_username else None,
                password=new_password,
                new_note=new_note if new_note else None
            )
            
            if self.session.save_vault():
                print_success("Entry updated")
                
                # Copy new password to clipboard if generated
                if new_password:
                    try:
                        pyperclip.copy(new_password)
                        print_info("New password copied to clipboard")
                    except:
                        pass
                
                return True
                
        except ValueError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Failed to update entry: {e}")
        
        return False
    
    def delete_entry(self, note: str = None):
        """Delete an entry from the vault"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        if not note:
            note = get_input("Title to delete: ")
            if not note:
                return False
        
        entry = self.session.vault.get_entry(note)
        if not entry:
            print_error(f"Entry '{note}' not found")
            return False
        
        # Confirm deletion
        if not confirm_action(f"Delete entry '{note}'?"):
            print_info("Cancelled")
            return False
        
        try:
            self.session.vault.delete_entry(note)
            if self.session.save_vault():
                print_success(f"Deleted entry '{note}'")
                return True
        except Exception as e:
            print_error(f"Failed to delete entry: {e}")
        
        return False
    
    def generate_password(self, length: int = 16, special_chars: bool = True, readable: bool = False, words: bool = False):
        """Generate a random password"""
        if not self.session.authenticated:
            print_error("Not authenticated. Please login first.")
            return False
        
        if readable or words:
            password = self.session.crypto.generate_readable_password(length, words)
        else:
            password = self.session.crypto.generate_password(length, special_chars)
        print_info(f"Generated password: {password}")
        
        try:
            pyperclip.copy(password)
            print_success("Password copied to clipboard")
        except:
            print_info("Could not copy to clipboard")
        
        return True