from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction
import base64

ALGOD_ADDRESS = "https://testnet-api.4160.nodely.dev"
ALGOD_TOKEN = ""

CREATOR_MNEMONIC = "father eye direct lava stay process tuna anger picture ahead differ hand habit hobby curious local book history trust arrow hidden broken bench abstract forward"

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

creator_private_key = mnemonic.to_private_key(CREATOR_MNEMONIC)
creator_address = account.address_from_private_key(creator_private_key)

print(f"Calling from address: {creator_address}")

account_info = algod_client.account_info(creator_address)
balance = account_info['amount'] / 1_000_000
print(f"Account balance: {balance} ALGO")

if balance < 0.1:
    print("Warning: Low balance. Get more ALGO from the faucet!")
    exit()

APP_ID = 749534825

print(f"Setting payment amount for App ID: {APP_ID}")

params = algod_client.suggested_params()

txn = transaction.ApplicationCallTxn(
    sender=creator_address,
    sp=params,
    index=APP_ID,
    on_complete=transaction.OnComplete.NoOpOC,
    app_args=["set_payment", (100).to_bytes(8, 'big')]
)

signed_txn = txn.sign(creator_private_key)

tx_id = algod_client.send_transaction(signed_txn)
print(f"Transaction sent! ID: {tx_id}")

print("Waiting for confirmation...")
confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)

print(f"Transaction confirmed in round {confirmed_txn['confirmed-round']}")
print(f"Payment amount set to 1 ALGO successfully!")
print(f"View transaction on Lora Explorer:")
print(f"https://lora.algokit.io/testnet/transaction/{tx_id}")
print(f"View application state:")
print(f"https://lora.algokit.io/testnet/application/{APP_ID}")
