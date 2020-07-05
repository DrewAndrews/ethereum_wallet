from web3 import Web3, HTTPProvider
from json import load, loads, dump
from time import sleep
import requests
import sys


with open("network.json") as network:
    data = load(network)
    rpcUrl = data["rpcUrl"]
    private_key = data["privKey"]
    gas_site = data["gasPriceUrl"]
    default_price = data["defaultGasPrice"]


web3 = Web3(HTTPProvider(rpcUrl))
account = web3.eth.account.privateKeyToAccount(private_key)


def deploy():
    balance = web3.eth.getBalance(account.address)
    with open("registrar.abi") as abi:
        reg_abi = abi.read()
    with open("registrar.bin") as bin:
        reg_bytecode = bin.read()
    with open("payments.abi") as abi:
        pay_abi = abi.read()
    with open("payments.bin") as bin:
        pay_bytecode = bin.read()

    contract_reg = web3.eth.contract(abi = reg_abi, bytecode = reg_bytecode)
    contract_pay = web3.eth.contract(abi = pay_abi, bytecode = pay_bytecode)

    headers = {"accept": "application/json"}
    data = requests.get(gas_site, headers)
    if data.status_code != 200:
        gas_price = default_price
    else:
        gas_price = int(data.json()["fast"] * 10**9)
        if balance < 1500000 * 2 * gas_price:
            print("No enough funds to send transaction")
            return

    tx_reg = contract_reg.constructor().buildTransaction({
        "from": account.address,
        "nonce": web3.eth.getTransactionCount(account.address),
        "gas": 1500000,
        "gasPrice": gas_price
    })
    singned_reg = account.signTransaction(tx_reg)
    regId = web3.eth.sendRawTransaction(singned_reg.rawTransaction)
    reg_reciept = web3.eth.waitForTransactionReceipt(regId)
    while reg_reciept['status'] != 1:
        sleep(0.1)
        reg_reciept = web3.eth.getTransactionReceipt(regId)
    reg_address = reg_reciept["contractAddress"]

    tx_pay = contract_pay.constructor().buildTransaction({
        "from": account.address,
        "nonce": web3.eth.getTransactionCount(account.address),
        "gas": 1500000,
        "gasPrice": gas_price
    })
    singned_pay = account.signTransaction(tx_pay)
    payId = web3.eth.sendRawTransaction(singned_pay.rawTransaction)
    pay_reciept = web3.eth.waitForTransactionReceipt(payId)
    while pay_reciept['status'] != 1:
        sleep(0.1)
        pay_reciept = web3.eth.getTransactionReceipt(payId)
    pay_address = pay_reciept["contractAddress"]
    print("KYC Registrar:", reg_address)
    print("Payment Handler:", pay_address)
    with open("registrar.json", 'w') as registrar:
        dump({"registrar": reg_address, "payments": pay_address}, registrar)

deploy()