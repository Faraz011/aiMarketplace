from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction
import base64

ALGOD_ADDRESS = "https://testnet-api.4160.nodely.dev"
ALGOD_TOKEN = ""

CREATOR_MNEMONIC = "father eye direct lava stay process tuna anger picture ahead differ hand habit hobby curious local book history trust arrow hidden broken bench abstract forward"

algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

creator_private_key = mnemonic.to_private_key(CREATOR_MNEMONIC)
creator_address = account.address_from_private_key(creator_private_key)

print(f"Deploying from address: {creator_address}")

account_info = algod_client.account_info("FR3MPW2NHLZL3V3EJMHNPCSHBRY5NM5JZLHIKU6YMBRS6Q5RQXDQOWKWOM")
balance = account_info['amount'] / 1_000_000
print(f"Account balance: {balance} ALGO")

if balance < 0.5:
    print("Warning: Low balance. Get more ALGO from the faucet!")
    exit()

with open("approval.teal", "r") as f:
    approval_program = f.read()

with open("clear.teal", "r") as f:
    clear_program = f.read()

approval_result = algod_client.compile(approval_program)
approval_bytes = base64.b64decode(approval_result['result'])

clear_result = algod_client.compile(clear_program)
clear_bytes = base64.b64decode(clear_result['result'])

print("Programs compiled successfully")

params = algod_client.suggested_params()

txn = transaction.ApplicationCreateTxn(
    sender=creator_address,
    sp=params,
    on_complete=transaction.OnComplete.NoOpOC,
    approval_program=approval_bytes,
    clear_program=clear_bytes,
    global_schema=transaction.StateSchema(num_uints=2, num_byte_slices=3),
    local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0)
)

params = algod_client.suggested_params()
txn = transaction.ApplicationCallTxn(
    sender=creator_address,
    sp=params,
    index=749534825,
    on_complete=transaction.OnComplete.NoOpOC,
    app_args=["set_payment", (1000000).to_bytes(8, 'big')]
)

signed_txn = txn.sign(creator_private_key)

tx_id = algod_client.send_transaction(signed_txn)
print(f"Transaction sent! ID: {tx_id}")

print("Waiting for confirmation...")
confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)

print(f"Transaction confirmed in round {confirmed_txn['confirmed-round']}")

app_id = confirmed_txn['application-index']
print(f"Smart Contract Deployed Successfully!")
print(f"Application ID: {app_id}")
print(f"View on Lora Explorer:")
print(f"https://lora.algokit.io/testnet/application/{app_id}")
