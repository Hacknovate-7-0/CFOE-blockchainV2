from algosdk.v2client import algod
client = algod.AlgodClient('', 'https://testnet-api.algonode.cloud', headers={'User-Agent': 'algosdk'})
info = client.account_info('4KG534Q6BUNUNDJRA7XBUH4OXYYXXHYFEAEHO3TASHU22WRD3AGGLGR2Y4')
print('Balance:', info['amount'] / 1_000_000, 'ALGO')