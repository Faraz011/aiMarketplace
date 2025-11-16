from algosdk.v2client import algod


algod_address = "https://testnet-api.algonode.cloud"
algod_token = ""

client = algod.AlgodClient(algod_token, algod_address)

address = "FR3MPW2NHLZL3V3EJMHNPCSHBRY5NM5JZLHIKU6YMBRS6Q5RQXDQOWKWOM"

try:
    account_info = client.account_info(address)
    balance = account_info.get('amount', 0)
    print(f"Balance: {balance} microAlgos ({balance / 1_000_000} ALGOs)")
except Exception as e:
    print("Error:", e)
