class BankAccount:
    bank_name = "National Bank"
    min_balance = 0
    _total_accounts = 0

    def __init__(self, account_id, holder_name, balance):
        self._validate(account_id, holder_name, balance)
        self.account_id = account_id
        self.holder_name = holder_name
        self.balance = balance
        BankAccount._total_accounts += 1

    @classmethod
    def set_bank_name(cls, name):
        cls.bank_name = name

    @classmethod
    def set_min_balance(cls, amount):
        cls.min_balance = amount

    @classmethod
    def get_total_accounts(cls):
        return cls._total_accounts

    @staticmethod
    def _validate(account_id, holder_name, balance):
        if not account_id or not isinstance(account_id, str):
            raise ValueError("Invalid account ID.")
        if not holder_name or not isinstance(holder_name, str):
            raise ValueError("Invalid account holder name.")
        if not isinstance(balance, (int, float)) or balance < 0:
            raise ValueError("Invalid initial balance.")

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance - amount < self.min_balance:
            return False
        self.balance -= amount
        return True

    def get_balance(self):
        return self.balance

    def __str__(self):
        return f"Account[{self.account_id}] - {self.holder_name} | Balance: ${self.balance:.2f}"

class SavingsAccount(BankAccount):
    def __init__(self, account_id, holder_name, balance, interest_rate):
        super().__init__(account_id, holder_name, balance)
        if not isinstance(interest_rate, (int, float)) or interest_rate < 0:
            raise ValueError("Invalid interest rate.")
        self.interest_rate = interest_rate

    def calculate_monthly_interest(self):
        return self.balance * (self.interest_rate / 100) / 12

    def __str__(self):
        return (f"SavingsAccount[{self.account_id}] - {self.holder_name} | "
                f"Balance: ${self.balance:.2f} | Interest Rate: {self.interest_rate}%")

class CheckingAccount(BankAccount):
    def __init__(self, account_id, holder_name, balance, overdraft_limit):
        super().__init__(account_id, holder_name, balance)
        if not isinstance(overdraft_limit, (int, float)) or overdraft_limit < 0:
            raise ValueError("Invalid overdraft limit.")
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance - amount < -self.overdraft_limit:
            return False
        self.balance -= amount
        return True

    def __str__(self):
        return (f"CheckingAccount[{self.account_id}] - {self.holder_name} | "
                f"Balance: ${self.balance:.2f} | Overdraft Limit: ${self.overdraft_limit:.2f}")


if __name__ == "__main__":
    savings_account = SavingsAccount("SA001", "Alice Johnson", 1000, 2.5)
    checking_account = CheckingAccount("CA001", "Bob Smith", 500, 200)
    print(savings_account)
    print(checking_account)

    print("Savings balance:", savings_account.get_balance())
    savings_account.deposit(500)
    print("After deposit:", savings_account.get_balance())
    result = savings_account.withdraw(200)
    print("Withdraw 200:", "Success" if result else "Failed", "| Balance:", savings_account.get_balance())

    print("Checking balance:", checking_account.get_balance())
    result = checking_account.withdraw(600)
    print("Withdraw 600 (overdraft):", "Success" if result else "Failed", "| Balance:", checking_account.get_balance())

    print("Monthly interest earned:", savings_account.calculate_monthly_interest())

    print("Total accounts created:", BankAccount.get_total_accounts())
    print("Bank name:", BankAccount.bank_name)

    BankAccount.set_bank_name("New National Bank")
    BankAccount.set_min_balance(100)
    print("Updated bank name:", BankAccount.bank_name)
    print("Updated minimum balance:", BankAccount.min_balance)

    try:
        invalid_account = SavingsAccount("SA002", "", -100, 1.5)
    except ValueError as e:
        print("Validation error:", e)
