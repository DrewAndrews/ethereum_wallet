from web3 import Web3, HTTPProvider
from json import load, loads
from sha3 import keccak_256
import requests
from time import sleep
from datetime import datetime
import sys
import faceid


with open("network.json") as network:
    data = load(network)
    rpcUrl = data["rpcUrl"]
    private_key = data["privKey"]
    gas_url = data["gasPriceUrl"]
    default_price = data["defaultGasPrice"]

with open("registrar.abi") as abi:
    reg_abi = abi.read()
with open("registrar.bin") as bin:
    reg_bytecode = bin.read()
with open("payments.abi") as abi:
    pay_abi = abi.read()
with open("payments.bin") as bin:
    pay_bytecode = bin.read()

with open("person.json") as face:
    data = load(face)
    person_id = data["personID"]

with open("registrar.json") as registrar:
    data = load(registrar)
    address_reg = data["registrar"]
    address_pay = data["payments"]

with open("person.json") as person:
    data = load(person)
    person_id = data["personID"]


web3 = Web3(HTTPProvider(rpcUrl))

def convert(balance):
	if balance == 0:
		return str(balance) + " poa"
	if balance < 10**3:
		return str(balance) + " wei"
	elif balance < 10**6:
		balance = balance / 10**3
		if len(str(balance)) > 8:
			return "{0:.6f}".format(balance).rstrip('0').rstrip(".") + " kwei"
		return str(balance) + " kwei"
	elif balance < 10**9:
		balance = balance / 10**6
		if len(str(balance)) > 8:
			return "{0:.6f}".format(balance).rstrip('0').rstrip(".") + " mwei"
		return str(balance) + " mwei"
	elif balance < 10**12:
		balance = balance / 10**9
		if len(str(balance)) > 8:
			return "{0:.6f}".format(balance).rstrip('0').rstrip(".") + " gwei"
		return str(balance) + " gwei"
	elif balance < 10**15:
		balance = balance / 10**12
		if len(str(balance)) > 8:
			return "{0:.6f}".format(balance).rstrip('0').rstrip(".") + " szabo"
		return str(balance) + " szabo"
	elif balance < 10**18:
		balance = balance / 10**15
		if len(str(balance)) > 8:
			return "{0:.6f}".format(balance).rstrip('0').rstrip(".") + " finney"
		return str(balance) + " finney"
	else:
		balance = balance / 10**18
		if len(str(balance)) > 8:
			return "{0:.6f}".format(balance).rstrip('0').rstrip(".") + " poa"
		return str(balance) + " poa"


def make_ID(ID):
	sum = ""
	for i in range(5):
		sum += ID[i]
	return int(sum, 16).to_bytes(16, "big")


def num_pin(pin_code, num):
	return int(pin_code[num]).to_bytes(1, "big")


def make_private_key_from_id(ID, pin_code):
	m = make_ID(ID)
	private_key = keccak_256("".encode("utf-8")).digest()
	private_key = keccak_256(private_key + m + num_pin(pin_code, 0)).digest()
	private_key = keccak_256(private_key + m + num_pin(pin_code, 1)).digest()
	private_key = keccak_256(private_key + m + num_pin(pin_code, 2)).digest()
	private_key = keccak_256(private_key + m + num_pin(pin_code, 3)).digest()
	private_key = hex(int.from_bytes(private_key, "big"))[2:]
	return private_key


def add_number(pin_code, phone_number):
    private_key = make_private_key_from_id(person_id, pin_code)
    account = web3.eth.account.privateKeyToAccount(private_key)
    balance = web3.eth.getBalance(account.address)

    headers = {"accept": "application/json"}
    data = requests.get(gas_url, headers)
    if data.status_code != 200:
        gas_price = default_price
    else:
        gas_price = int(data.json()["fast"] * 10**9)
        if balance < 100000 * gas_price:
            print("Not enough funds to add phone number")
            return

    contract_reg = web3.eth.contract(address = address_reg, abi = reg_abi)

    if contract_reg.functions.get_address(phone_number).call() != "0x0000000000000000000000000000000000000000":
        print('This phone number is registered')
        return

    gas_reg = 100000
    tx_reg = {
        "from": account.address, 
        "nonce": web3.eth.getTransactionCount(account.address),
        "gas": gas_reg,
        "gasPrice": gas_price
    }
    tx_to_sign = contract_reg.functions.create_user(phone_number).buildTransaction(tx_reg)
    signed_tx = account.signTransaction(tx_to_sign)
    tx_id = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_reciept = web3.eth.waitForTransactionReceipt(tx_id)
    print("Your phone number is added!")
    print("Transaction Hash:", tx_reciept["transactionHash"].hex())


def delete_user(pin_code):
    private_key = make_private_key_from_id(person_id, pin_code)
    account = web3.eth.account.privateKeyToAccount(private_key)
    balance = web3.eth.getBalance(account.address)

    headers = {"accept": "application/json"}
    data = requests.get(gas_url, headers)
    if data.status_code != 200:
        gas_price = default_price
    else:
        gas_price = int(data.json()["fast"] * 10**9)
        if balance < 100000 * gas_price:
            print("Not enough funds to add phone number")
            return

    contract_reg = web3.eth.contract(address = address_reg, abi = reg_abi)

    number = str(contract_reg.functions.get_number(account.address).call())
    number = number[number.find("'") + 1:number.rfind("'")]
    if number == "":
        print("You are not registered")
        return
    tx_del = {
        "from": account.address, 
        "nonce": web3.eth.getTransactionCount(account.address),
        "gas": 150000,
        "gasPrice": gas_price
    }
    tx_to_sign = contract_reg.functions.delete_user(number).buildTransaction(tx_del)
    signed_tx = account.signTransaction(tx_to_sign)
    tx_id = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_reciept = web3.eth.waitForTransactionReceipt(tx_id)
    while tx_reciept["status"] != 1:
        sleep(0.1)
        tx_reciept = web3.eth.getTransactionFromBlock(tx_id)
    print("Your phone number is deleted!")
    print("Transaction Hash:", tx_reciept["transactionHash"].hex())
    

def make_transaction(pin_code, phone_number, value):
    private_key = make_private_key_from_id(person_id, pin_code)
    account = web3.eth.account.privateKeyToAccount(private_key)
    balance = web3.eth.getBalance(account.address)

    contract_reg = web3.eth.contract(address = address_reg, abi = reg_abi)

    if contract_reg.functions.get_address(phone_number).call() == "0x0000000000000000000000000000000000000000":
        print('This phone number does not exist')
        return
    else:
        reciever = contract_reg.functions.get_address(phone_number).call()  
        headers = {"accept": "application/json"}
        data = requests.get(gas_url, headers)
        gas = web3.eth.estimateGas({"to": reciever, "value": value})
        if data.status_code != 200:
            gas_price = default_price
        else:
            gas_price = int(data.json()["fast"] * 10**9)
        if balance < gas * gas_price:
            print("Not enough funds to send this value")
            return

        tx = {
            "to": reciever,
            "nonce": web3.eth.getTransactionCount(account.address),
            "gas": gas,
            "gasPrice": gas_price,
            "value": int(value)
        }
        sign = account.signTransaction(tx)
        tx_id = web3.eth.sendRawTransaction(sign.rawTransaction)
        tx_reciept = web3.eth.waitForTransactionReceipt(tx_id)
        while tx_reciept["status"] != 1:
            sleep(0.1)
            tx_reciept = web3.eth.getTransactionReceipt(tx_id)
#########################################################################################################################
        contract_pay = web3.eth.contract(address = address_pay, abi = pay_abi)
        
        tx_pay = {
            "from": account.address,
            "nonce": web3.eth.getTransactionCount(account.address),
            "gas": 1500000,
            "gasPrice": gas_price
        }
        tx_bytes = web3.toBytes(tx_reciept["transactionHash"])

        to_signed_pay = contract_pay.functions.add_payment(account.address, reciever, tx_bytes).buildTransaction(tx_pay)

        signed_tx = account.signTransaction(to_signed_pay)

        pay_id = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        pay_reciept = web3.eth.waitForTransactionReceipt(pay_id)
        while pay_reciept["status"] != 1:
            sleep(0.1)
            pay_reciept = web3.eth.getTransactionReceipt(pay_id)

        print("""Payment of {} to {} scheduled""".format(convert(int(value)), phone_number))
        print("Transaction Hash:", tx_reciept["transactionHash"].hex())
        print("Your transaction added to your payments list!")
        print("Payment added:", pay_reciept["transactionHash"].hex())


def show_payments(pin_code):
    private_key = make_private_key_from_id(person_id, pin_code)
    account = web3.eth.account.privateKeyToAccount(private_key)

    contract_reg = web3.eth.contract(address = address_reg, abi = reg_abi)
    contract_pay = web3.eth.contract(address = address_pay, abi = pay_abi)

    if contract_reg.functions.get_number(account.address).call() == "":
        print('This phone number does not exist')
        return
    
    payments = contract_pay.functions.get_payments_list(account.address).call()
    for payment in payments:
        data = web3.eth.getTransaction(payment.hex())
        if data["from"] == account.address: 
            time_sending = datetime.fromtimestamp(web3.eth.getBlock(data["blockNumber"])["timestamp"])
            to = str(contract_reg.functions.get_number(data["to"]).call())
            to = to[to.find("'") + 1:to.rfind("'")]
            value = convert(int(data["value"]))
            print(time_sending, "TO:", to, "VALUE:", value)
        else:
            time_sending = datetime.fromtimestamp(web3.eth.getBlock(data["blockNumber"])["timestamp"])
            sender = str(contract_reg.functions.get_number(data["from"]).call())
            sender = sender[sender.find("'") + 1:sender.rfind("'")]
            value = convert(int(data["value"]))
            print(time_sending, "FROM:", sender, "VALUE:", value)


def get_balance(pin_code):
    private_key = make_private_key_from_id(person_id, pin_code)
    account = web3.eth.account.privateKeyToAccount(private_key)
    balance = web3.eth.getBalance(account.address)
    print("Your balance is", balance)

if len(sys.argv) == 1:
    pass
elif sys.argv[1] == "--add_number":
    pin_code = sys.argv[2]
    phone_number = sys.argv[3]
    add_number(pin_code, phone_number)
elif sys.argv[1] == "--delete_number":
    pin_code = int(sys.argv[2])
    delete_user(pin_code)
elif sys.argv[1] == "--send":
    pin_code = int(sys.argv[2])
    phone_number = sys.argv[3]
    value = sys.argv[4]
    make_transaction(pin_code, phone_number, value)
elif sys.argv[1] == "--payments":
    pin_code = int(sys.argv[2])
    show_payments(pin_code)
elif sys.argv[1] == "--balance":
    pin_code = int(sys.argv[2])
    get_balance(pin_code)