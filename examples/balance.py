from client_factory import create_client

client = create_client()

balance = client.balance().find().data
print(f"Total Balance: {balance.total_balance}")
print(f"Balance: {balance.balance}")
print(f"Credit: {balance.credit}")
