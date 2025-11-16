from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction

ALGOD_ADDRESS = "https://testnet-api.4160.nodely.dev"
ALGOD_TOKEN = ""

AGENT_MNEMONIC = "fluid vintage inspire matrix quarter paddle crater matrix wreck cube buddy opinion guess split erode teach base horse oxygen mouse decrease session icon absent memory"

APP_ID = 749534825

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

agent_private_key = mnemonic.to_private_key(AGENT_MNEMONIC)
agent_address = account.address_from_private_key(agent_private_key)

print(f"Agent registering task from: {agent_address}")

try:
    account_info = algod_client.account_info(agent_address)
    balance = account_info['amount'] / 1_000_000
    print(f"Agent balance: {balance} ALGO")
    
    if balance < 0.1:
        print("Warning: Low balance. Get ALGO from faucet!")
        print("Visit: https://bank.testnet.algorand.network/")
        exit()
except Exception as e:
    print(f"Error checking balance: {e}")
    exit()

params = algod_client.suggested_params()

result_hash = "EEKEGEY4GXP533SZLP5WHKVO4PBOKYXI5T7UJFISOAU7KPLFOE6HBJA32A"

agent_txn = transaction.ApplicationCallTxn(
    sender=agent_address,
    sp=params,
    index=APP_ID,
    on_complete=transaction.OnComplete.NoOpOC,
    app_args=["register_task", result_hash]
)

signed_txn = agent_txn.sign(agent_private_key)

tx_id = algod_client.send_transaction(signed_txn)
print(f"Transaction sent! ID: {tx_id}")

print("Waiting for confirmation...")
try:
    confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
    print(f"Transaction confirmed in round {confirmed_txn['confirmed-round']}")
    print(f"Task registered successfully!")
    print(f"Result Hash: {result_hash}")
    print(f"View transaction on Lora Explorer:")
    print(f"   https://lora.algokit.io/testnet/transaction/{tx_id}")
    print(f"View updated application state:")
    print(f"   https://lora.algokit.io/testnet/application/{APP_ID}")
except Exception as e:
    print(f"Error: {e}")
