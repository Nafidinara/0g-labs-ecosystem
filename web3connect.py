"""
Modul sederhana sebagai pengganti web3connect.
"""
from web3 import Web3
from eth_account import Account

def connect(private_key):
    """
    Fungsi sederhana untuk mengganti web3connect.connect()
    Mengembalikan alamat wallet berdasarkan private key
    """
    account = Account.from_key(private_key)
    return {
        'address': account.address,
        'privateKey': private_key
    }