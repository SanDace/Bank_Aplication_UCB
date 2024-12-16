import json
import os
import random
import smtplib
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import hashlib  # For hashing passwords
import sys
from tabulate import tabulate # For styling table
from colorama import Fore, Style, init # For adding colours


# Load environment variables from .env file
load_dotenv()

# File to store users and passwords
USERS_FILE = "users.json"

class UserManager:
    def __init__(self):
        self.user_data_file = USERS_FILE
        self.load_user_data()

    def load_user_data(self):
        if os.path.exists(self.user_data_file):
            with open(self.user_data_file, "r") as file:
                content = file.read().strip()
                self.users = json.loads(content) if content else []
        else:
            self.users = []

    def save_user_data(self):
        with open(self.user_data_file, "w") as file:
            json.dump(self.users, file, indent=4)

    def add_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        new_user = {"username": username, "password": hashed_password}
        self.users.append(new_user)
        self.save_user_data()

    def setup_initial_admin(self):
        if self.users:
            print("User data found. Proceeding to login.")
            return True
        print("No users found. Please set up an initial admin account.")
        username = input("Enter a username for the admin: ").strip()
        password = input("Enter a password for the admin: ").strip()

        if username and password:
            self.add_user(username, password)
            print(f"Admin user '{username}' created successfully!")
            return True
        else:
            print("Error: Username and password cannot be empty.")
            return False

    def login(self):
        while True:
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user = next((u for u in self.users if u["username"] == username 
            and u["password"] == hashed_password), None)

            if user:
                print("Login successful! Welcome!")
                return True
            else:
                print("Invalid username or password.")
                choice = input("Would you like to try again? (yes/no): ").strip().lower()
                while choice not in ["yes", "no"]:
                    choice = input("Please enter 'yes' or 'no': ").strip().lower()
                if choice == "no":
                    print("Exiting the program.")
                    sys.exit()

class Account:
    def __init__(self, name, account_number, email, initial_balance=0, account_type="Savings", 
                 street_address=None, postal_code=None, city=None, country=None):
        self._name = name # Can only be accessed through methods
        self._account_number = account_number
        self._email = email
        self._balance = initial_balance # Protected attribute
        self._account_type = account_type
        self._street_address = street_address
        self._postal_code = postal_code
        self._city = city
        self._country = country
        self._transactions = []
        # Modified to include running balance in the transaction entry
        self._transactions.append(self.create_timestamped_entry("Account created with balance", initial_balance, initial_balance))

    def deposit(self, amount):
        # Method controls how balance can be modified
        if amount > 0:
            self._balance += amount
            self._transactions.append(self.create_timestamped_entry("Deposit", amount, self._balance))
            print(f"Successfully deposited ${amount}")
            return True
        else:
            print("Invalid deposit amount. Please enter a positive number.")
            return False

    def withdraw(self, amount):
            # This should be overridden by child classes
            raise NotImplementedError("Withdraw method must be implemented by specific account types")

    def create_timestamped_entry(self, action, amount, running_balance):
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),  # Removed seconds
            "action": action,
            "amount": amount,
            "running_balance": running_balance,
            "details": f"{action}: ${amount}"  # For backward compatibility
        }

    def get_account_type(self):
        return self._account_type

    def check_balance(self):
        # Format the balance with commas and 2 decimal places
        formatted_balance = f"${self._balance:,.2f}"

        # Stylish output
        return self.print_balance_details(formatted_balance)

    def print_balance_details(self, formatted_balance):
          # Format the balance success message in an attractive way
          account_info = f"Account Holder Name: {self._name}"
          balance_info = f"Current balance: {formatted_balance}"

          # Border based on the length of the content
          border = "+" + "-" * (len(account_info) + 4) + "+"
          
          # Attractive display
          output = f"\n{border}\n"
          output += f"{Fore.CYAN}| {account_info} |{Fore.RESET}\n"  # Account holder name
          output += f"{Fore.GREEN}| {balance_info} |{Fore.RESET}\n"  # Current balance
          output += f"{border}\n"
          return output

    def show_transaction_history(self):
        if not self._transactions:
            print("\nNo transactions to display.")
            return

        # Print account header information
        print("\n" + "="*50)
        print(f"Account Statement")
        print("="*50)
        print(f"Account Number: {self._account_number}")
        print(f"Account Holder: {self._name}")
        print(f"Account Type: {self._account_type}")
        print(f"Current Balance: ${self._balance:.2f}")
        print("="*50 + "\n")

        # Prepare data for tabulate
        headers = ["Date & Time", "Transaction", "Amount", "Balance"]
        rows = []
        running_balance = 0
        
        for trans in self._transactions:
            # Handle both old and new transaction formats
            timestamp = trans.get('timestamp', '')
            
            # Parse the details string for old format transactions
            if 'action' not in trans:
                details = trans.get('details', '')
                if "Account created with balance" in details:
                    action = "Account created"
                    amount = float(details.split('$')[1])
                    running_balance = amount
                elif "Deposited" in details:
                    action = "Deposit"
                    amount = float(details.split('$')[1])
                    running_balance += amount
                elif "Withdrew" in details:
                    action = "Withdrawal"
                    amount = float(details.split('$')[1])
                    running_balance -= amount
            else:
                action = trans['action']
                amount = trans['amount']
                running_balance = trans.get('running_balance', running_balance)

            # Format amount string
            if "Withdrawal" in action:
                amount_str = f"-${amount:.2f}"
            else:
                amount_str = f"${amount:.2f}"

            rows.append([
                timestamp,
                action,
                amount_str,
                f"${running_balance:.2f}"
            ])

        # Print formatted table
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid", numalign="right"))
        
        # Print summary footer
        print("\nStatement Summary:")
        print(f"Opening Balance: ${float(rows[0][3].replace('$', '')):.2f}")
        print(f"Closing Balance: ${self._balance:.2f}")
        print(f"Total Transactions: {len(self._transactions) - 1}")  # Subtract 1 to exclude account creation
        print("="*50)

    def to_dict(self):
        return {
            "name": self._name,
            "account_number": self._account_number,
            "email": self._email,
            "balance": self._balance,
            "account_type": self._account_type,
            # New address attributes in dictionary representation
            "street_address": self._street_address,
            "postal_code": self._postal_code,
            "city": self._city,
            "country": self._country,
            "transactions": self._transactions,
        }

    @staticmethod
    def from_dict(data):
        if data.get("account_type") == "Savings":
            return SavingsAccount.from_dict(data)
        elif data.get("account_type") == "Checking":
            return CheckingAccount.from_dict(data)
        else:
            account = Account(
                data.get("name"),
                data.get("account_number"),
                data.get("email"),
                data.get("balance", 0),
                data.get("account_type", "Savings"),
                data.get("street_address"),
                data.get("postal_code"),
                data.get("city"),
                data.get("country")
            )
            account._transactions = data.get("transactions", [])
            return account

class SavingsAccount(Account):
    WITHDRAWAL_LIMIT = 100  # $100 limit for savings accounts

    def __init__(self, name, account_number, email, initial_balance=0, 
                 street_address=None, postal_code=None, city=None, country=None):
                 # Inherits from parent class
        super().__init__(name, account_number, email, initial_balance, 
                         account_type="Savings", 
                         street_address=street_address, 
                         postal_code=postal_code, 
                         city=city, 
                         country=country)

    def withdraw(self, amount):
        if amount > self.WITHDRAWAL_LIMIT:
            print(f"Withdrawal limit exceeded! The maximum you can withdraw is ${self.WITHDRAWAL_LIMIT}.")
            return False

        if amount > 0 and amount <= self._balance:
            self._balance -= amount
            self._transactions.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "Withdrawal",
                "amount": amount,
                "running_balance": self._balance,
                "details": f"Withdrawal: ${amount}"
            })
            print(f"Successfully withdrew ${amount} from Savings Account.")
            return True
        else:
            print("Invalid withdrawal amount or insufficient funds in Savings Account.")
            return False

    @staticmethod
    def from_dict(data):
        account = SavingsAccount(
            data.get("name"),
            data.get("account_number"),
            data.get("email"),
            data.get("balance", 0),
            data.get("street_address"),
            data.get("postal_code"),
            data.get("city"),
            data.get("country")
        )
        account._transactions = data.get("transactions", [])
        return account

class CheckingAccount(Account):
    def __init__(self, name, account_number, email, initial_balance=0, 
                 street_address=None, postal_code=None, city=None, country=None):
                 # Inherits from parent class
        super().__init__(name, account_number, email, initial_balance, 
                         account_type="Checking", 
                         street_address=street_address, 
                         postal_code=postal_code, 
                         city=city, 
                         country=country)

    def withdraw(self, amount):
        if amount > 0 and amount <= self._balance:
            self._balance -= amount
            self._transactions.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "Withdrawal",
                "amount": amount,
                "running_balance": self._balance,
                "details": f"Withdrawal: ${amount}"
            })
            print(f"Successfully withdrew ${amount} from Checking Account.")
            return True
        else:
            print("Invalid withdrawal amount or insufficient funds in Checking Account.")
            return False

    @staticmethod
    def from_dict(data):
        account = CheckingAccount(
            data.get("name"),
            data.get("account_number"),
            data.get("email"),
            data.get("balance", 0),
            data.get("street_address"),
            data.get("postal_code"),
            data.get("city"),
            data.get("country")
        )
        account._transactions = data.get("transactions", [])
        return account
    
    def __init__(self, name, account_number, email, initial_balance=0, 
                 street_address=None, postal_code=None, city=None, country=None):
        super().__init__(name, account_number, email, initial_balance, 
                         account_type="Checking", 
                         street_address=street_address, 
                         postal_code=postal_code, 
                         city=city, 
                         country=country)

    @staticmethod
    def from_dict(data):
        account = CheckingAccount(
            data.get("name"),
            data.get("account_number"),
            data.get("email"),
            data.get("balance", 0),
            data.get("street_address"),
            data.get("postal_code"),
            data.get("city"),
            data.get("country")
        )
        account._transactions = data.get("transactions", [])
        return account
# Bank class to handle accounts and transactions
class Bank:

    def __init__(self):
        self.accounts = {}
        self.load_data()

    def save_data(self):
        data = {acc_num: acc.to_dict() for acc_num, acc in self.accounts.items()}
        with open("bank_data.json", "w") as file:
            json.dump(data, file, indent=4) #indent for spacing in json  file
        print("Data saved successfully!")

    def generate_account_number(self):
        while True:
            account_number = str(random.randint(1000000000, 9999999999))
            if account_number not in self.accounts:
                return account_number



    def create_account(self, name, email, account_type, initial_balance=0, 
                    street_address=None, postal_code=None, city=None, country=None):
        # Email validation using a regex pattern
        email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_pattern, email):
            print("Error: Invalid email format.")
            return 

        if email in [acc.to_dict()["email"] for acc in self.accounts.values()]:
            print("Error: An account with this email already exists!")
            return

        if not name or not email:
            print("Error: Name and email cannot be empty!")
            return

        if initial_balance < 0:
            print("Error: Initial balance cannot be negative.")
            return

        if account_type not in ["Checking", "Savings"]:
            print("Error: Account type must be either 'Checking' or 'Savings'.")
            return 

        account_number = self.generate_account_number()

        # Instantiate CheckingAccount or SavingsAccount with address parameters
        if account_type == "Checking":
            new_account = CheckingAccount(
                name, account_number, email, initial_balance, 
                street_address=street_address, 
                postal_code=postal_code, 
                city=city, 
                country=country
            )
        else:
            new_account = SavingsAccount(
                name, account_number, email, initial_balance, 
                street_address=street_address, 
                postal_code=postal_code, 
                city=city, 
                country=country
            )

        self.accounts[account_number] = new_account
        self.save_data()
        print(f"Account created for {name} with account number {account_number} as a {account_type} account.")
        self.send_account_details(email, name, account_number, initial_balance)

    def update_account_details(self, account_number):
        # Find the account
        account = self.get_account(account_number)
        if not account:
            print("Account not found.")
            return

        # Convert account to dictionary to access current details
        current_details = account.to_dict()

        print("\nUpdate Account Details")
        print("Current Information:")
        print(f"Name: {current_details['name']}")
        print(f"Email: {current_details['email']}")
        print(f"Street Address: {current_details.get('street_address', 'N/A')}")
        print(f"Postal Code: {current_details.get('postal_code', 'N/A')}")
        print(f"City: {current_details.get('city', 'N/A')}")
        print(f"Country: {current_details.get('country', 'N/A')}")

        # Name update
        new_name = input("Enter new name (press Enter to keep current): ").strip()
        if new_name:
            # Add name validation
            account._name = new_name

        # Email update with validation
        while True:
            new_email = input("Enter new email (press Enter to keep current): ").strip()
            if not new_email:
                break
            
            # Email validation pattern
            email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
            if not re.match(email_pattern, new_email):
                print("Invalid email format. Please try again.")
                continue
            
            # Check if email is already in use by another account
            if any(acc.to_dict()["email"] == new_email and acc != account for acc in self.accounts.values()):
                print("This email is already associated with another account. Please use a different email.")
                continue
            
            account._email = new_email
            break

        # Address updates
        new_street_address = input("Enter new street address (press Enter to keep current): ").strip()
        if new_street_address:
            if len(new_street_address) < 5:
                print("Street address must be at least 5 characters long. Update cancelled.")
            else:
                account._street_address = new_street_address

        new_postal_code = input("Enter new postal code (press Enter to keep current): ").strip()
        if new_postal_code:
            if len(new_postal_code) < 3:
                print("Postal code must be at least 3 characters long. Update cancelled.")
            else:
                account._postal_code = new_postal_code

        new_city = input("Enter new city (press Enter to keep current): ").strip()
        if new_city:
            if len(new_city) < 3:
                print("City must be at least 3 characters long. Update cancelled.")
            else:
                account._city = new_city

        new_country = input("Enter new country (press Enter to keep current): ").strip()
        if new_country:
            if len(new_country) < 3:
                print("Country must be at least 3 characters long. Update cancelled.")
            else:
                account._country = new_country

        # Save updated data
        self.save_data()
        print("Account details updated successfully!")





    def get_account(self, account_number):
        return self.accounts.get(account_number, None)

  
        data = {acc_num: acc.to_dict() for acc_num, acc in self.accounts.items()}
        with open("bank_data.json", "w") as file:
            json.dump(data, file, indent=4)
        print("Data saved successfully!")

    def load_data(self):
        if os.path.exists("bank_data.json"):
            try:
                with open("bank_data.json", "r") as file:
                    data = json.load(file)
                    if data:
                        self.accounts = {}
                        for acc_num, acc_data in data.items():
                            # Use the appropriate class's from_dict method
                            self.accounts[acc_num] = Account.from_dict(acc_data)

                        print("Data loaded successfully!")
                        
                    else:
                        print("The bank_data.json file is empty. Starting fresh.")
            except json.JSONDecodeError:
                print("Error reading the bank_data.json file. Starting fresh.")
                self.accounts = {}
        else:
            print("No existing data found, starting fresh.")
            self.accounts = {}

    def send_account_details(self, email, name, account_number, balance):
        sender_email = os.getenv("SENDER_EMAIL")# stored in .env 
        sender_password = os.getenv("SENDER_PASSWORD") #stored in .env
        subject = "Your New Bank Account Details"

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = email
        message["Subject"] = subject 
       # html code will be displayed in the mail 
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Hello {name},</h2>
                <p>Your bank account has been successfully created with the following details:</p>
                <ul>
                    <li><strong>Account Number:</strong> {account_number}</li>
                    <li><strong>Initial Balance:</strong> ${balance}</li>
                </ul>
            </body>
        </html>
        """
        message.attach(MIMEText(html_content, "html"))
        #will try to send the mail
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
            server.quit()
            print(f"Account details email sent to {email}.")
        except Exception as e:
            print(f"Failed to send email. Error: {str(e)}")

    def display_accounts_by_type(self):
        while True:
            print("\nDisplay Accounts By Type:")
            print("1. All Accounts")
            print("2. Checking Accounts")
            print("3. Savings Accounts")
            print("4. Exit to Main Menu")
            sub_choice = input("Enter your choice: ").strip()

            if sub_choice == "1":
                self.display_all_accounts()
            elif sub_choice == "2":
                self.display_specific_accounts("Checking")
            elif sub_choice == "3":
                self.display_specific_accounts("Savings")
            elif sub_choice == "4":
                print("Returning to the main menu.")
                break
            else:
                print("Invalid choice, please try again.")

    def display_all_accounts(self):
        if not self.accounts:
            print("\nNo accounts available to display.")
            return

        print("\nAll Accounts:")
        self.print_accounts_table(self.accounts.values())

    def display_specific_accounts(self, account_type):
        filtered_accounts = [acc for acc in self.accounts.values() if acc.get_account_type() == account_type]
        if not filtered_accounts:
            print(f"\nNo {account_type} accounts available to display.")
            return

        print(f"\n{account_type} Accounts:")
        self.print_accounts_table(filtered_accounts)

    def print_accounts_table(self, accounts):
        # Define table headers
        headers = ["Name", "Account Number", "Email", "Balance", "Account Type"]

        # Create table rows by extracting account details
        rows = [
            [
                acc.to_dict()["name"],
                acc.to_dict()["account_number"],
                acc.to_dict()["email"],
                f"${acc.to_dict()['balance']:.2f}",
                acc.to_dict()["account_type"]
            ]
            for acc in accounts
        ]

        # Print the table using tabulate
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    def view_transaction_history(self):
        account_number = input("Enter the account number to view transaction history: ").strip()
        account = self.get_account(account_number)
        if account:
            account.show_transaction_history()
        else:
            print("Account not found.")

def main():
    user_manager = UserManager()

    # Attempt to set up the initial admin if no users exist
    if user_manager.setup_initial_admin():
        # Proceed with login if setup was successful
        user_manager.login()

    bank = Bank()

    def print_menu():
        print(Fore.CYAN + "=" * 40)
        print(Fore.YELLOW + "        Welcome to MY bank System        ")
        print(Fore.CYAN + "=" * 40)
        print(Fore.GREEN + "1. Create Account" + Fore.RESET)
        print(Fore.MAGENTA + "2. Deposit" + Fore.RESET)
        print(Fore.BLUE + "3. Withdraw" + Fore.RESET)
        print(Fore.RED + "4. Check Balance" + Fore.RESET)
        print(Fore.YELLOW + "5. Transaction History" + Fore.RESET)
        print(Fore.CYAN + "6. Display Accounts by Type" + Fore.RESET)
        print(Fore.GREEN + "7. Update Account Details" + Fore.RESET)  
        print(Fore.RED + "8. Exit" + Fore.RESET)  #exit the program
        print(Fore.CYAN + "=" * 40 + Fore.RESET)

    while True:
        print("\n")
        print_menu()
        choice = input(Fore.LIGHTWHITE_EX + "Enter your choice: " + Fore.RESET).strip()

        if choice == "1":
            # Account holder's name
            name = input("Enter account holder's name: ").strip()
            while not name:
                print("Name cannot be empty. Please enter a valid name.")
                name = input("Enter account holder's name: ").strip()

            # Account holder's email with validation
            email = input("Enter account holder's email: ").strip()
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            while not re.match(email_pattern, email):
                print("Invalid email format. Please enter a valid email address.")
                email = input("Enter account holder's email: ").strip()

            # Account type (Checking or Savings)
            account_type = input("Enter account type (Checking/Savings): ").capitalize()
            while account_type not in ["Checking", "Savings"]:
                print("Invalid choice. Please enter either 'Checking' or 'Savings'.")
                account_type = input("Enter account type (Checking/Savings): ").capitalize()

            # Initial deposit amount with validation
            while True:
                try:
                    initial_balance = float(input("Enter initial deposit amount: "))
                    if initial_balance < 0:
                        print("Initial deposit cannot be negative. Please enter a valid amount.")
                    else:
                        break  # Exit the loop once a valid amount is entered
                except ValueError:
                    print("Invalid amount. Please enter a numeric value.")

            
            # Address validation
            while True:
                street_address = input("Enter street address (required, at least 5 characters): ").strip()
                if len(street_address) < 5:
                    print("Street address must be at least 5 characters long. Please enter a valid address.")
                else:
                    break

            while True:
                postal_code = input("Enter postal code (required): ").strip()
                if len(postal_code) < 6:  # Adjust this condition based on postal code format in your region
                    print("Postal code must be at least 3 characters long. Please enter a valid postal code.")
                else:
                    break

            while True:
                city = input("Enter city (required, at least 3 characters): ").strip()
                if len(city) < 5:
                    print("City must be at least 3 characters long. Please enter a valid city.")
                else:
                    break

            while True:
                country = input("Enter country (required, at least 3 characters): ").strip()
                if len(country) < 5:
                    print("Country must be at least 3 characters long. Please enter a valid country.")
                else:
                    break


            # Check if an account with the same email already exists
            if any(acc.to_dict()["email"] == email for acc in bank.accounts.values()):
                print("An account with this email already exists. Please try again with a different email.")
            else:
                # Create the account if all validations pass
                bank.create_account(
                    name, email, account_type, initial_balance, 
                    street_address=street_address, 
                    postal_code=postal_code, 
                    city=city, 
                    country=country
                )
                print(f"Account successfully created for {name}.")

        elif choice == "2":
            account_number = input("Enter your account number: ").strip()
            account = bank.get_account(account_number)
            if account:
                try:
                    amount = float(input("Enter amount to deposit: "))
                except ValueError:
                    print("Invalid amount. Please enter a numeric value.")
                    continue
                account.deposit(amount)
                bank.save_data()
            else:
                print("Account not found.")

        elif choice == "3":
            account_number = input("Enter your account number: ").strip()
            account = bank.get_account(account_number)
            
            if account:
                try:
                    amount = float(input("Enter amount to withdraw: "))
                    if account.withdraw(amount):  # if withdrawal is successful
                        bank.save_data()  # Use the updated save_data method
                except ValueError:
                    print("Invalid amount. Please enter a numeric value.")
            else:
                print("Account not found.")

        elif choice == "4":
            account_number = input("Enter your account number: ").strip()
            account = bank.get_account(account_number)
            if account:
                print(account.check_balance())
            else:
                print("Account not found.")
        elif choice == "5":
                account_number = input("Enter your account number: ").strip()
                account = bank.get_account(account_number)
                if account:
                    account.show_transaction_history()
                else:
                    print("Account not found.")
    
        elif choice == "6":
            bank.display_accounts_by_type()

        elif choice == "7":
            account_number = input("Enter the account number to update: ").strip()
            bank.update_account_details(account_number)

        elif choice == "8":
            print("Exiting the program.")
            break

        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()



    