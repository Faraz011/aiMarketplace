from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction

ALGOD_ADDRESS = "https://testnet-api.4160.nodely.dev"
ALGOD_TOKEN = ""

CREATOR_MNEMONIC = "father eye direct lava stay process tuna anger picture ahead differ hand habit hobby curious local book history trust arrow hidden broken bench abstract forward"

APP_ID = 749534825
AGENT_ADDRESS = "EEKEGEY4GXP533SZLP5WHKVO4PBOKYXI5T7UJFISOAU7KPLFOE6HBJA32A"

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

creator_private_key = mnemonic.to_private_key(CREATOR_MNEMONIC)
creator_address = account.address_from_private_key(creator_private_key)

print(f"Creator approving task from: {creator_address}")
print(f"Payment will be sent to agent: {AGENT_ADDRESS}")

params = algod_client.suggested_params()

approve_txn = transaction.ApplicationCallTxn(
    sender=creator_address,
    sp=params,
    index=APP_ID,
    on_complete=transaction.OnComplete.NoOpOC,
    app_args=["approve_and_release"],
    accounts=[AGENT_ADDRESS]
)

signed_txn = approve_txn.sign(creator_private_key)

try:
    tx_id = algod_client.send_transaction(signed_txn)
    print(f"\nApproval transaction sent! ID: {tx_id}")
    
    print("Waiting for confirmation...")
    confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
    
    print(f"\nSuccess! Confirmed in round {confirmed_txn['confirmed-round']}")
    print(f"\nTask approved and 1 ALGO sent to agent!")
    
    agent_info = algod_client.account_info(AGENT_ADDRESS)
    agent_balance = agent_info['amount'] / 1_000_000
    print(f"\nAgent balance: {agent_balance} ALGO")
    
    print(f"\nView transaction:")
    print(f"   https://lora.algokit.io/testnet/transaction/{tx_id}")
    print(f"\nView contract state:")
    print(f"   https://lora.algokit.io/testnet/application/{APP_ID}")
    
except Exception as e:
    print(f"\nError: {e}")
    
    if "overspend" in str(e):
        print("\nThe contract account needs funding!")
        print("Run the funding script first to send ALGO to the contract.")
