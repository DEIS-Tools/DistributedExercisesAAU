import math
import random
import sys
import os

from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub
from cryptography.hazmat.primitives import hashes

from hashlib import sha256
import json
import time





class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def to_string(self):
        return f"index: {self.index}; transactions {self.transactions}; timestamp {self.timestamp}; previous_hash {self.previous_hash} nonce {self.nonce} hash {self.hash}"

    @property
    def hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    @property
    def hash_binary(self):
        return "{0:0256b}".format(int(self.hash, 16))



class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        # the genesis block is empty (no transactions) and has a previous_block = 0
        # it must be created by one miner only
        genesis_block = Block(0, [], time.time(), "0")
        self.chain.append(genesis_block)
        print("genesis: " + genesis_block.to_string())

    @property
    def last_block(self):
        if len(self.chain) == 0:
            return None
        return self.chain[-1]

    difficulty = 4
    # TODO: set difficulty to 2, to have many more forks.
    # TODO: understand why having lower difficulty leads to more forks.
    def proof_of_work(self, block):
        computed_hash_binary = block.hash_binary
        if not computed_hash_binary.startswith('0' * Blockchain.difficulty):
            return False
        return True

    def add_block(self, block):
        # I add the block to the blockchain, but only if:
        #   it points to the previous existing block, and
        #   the block has a valid proof of work
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False
        if not self.proof_of_work(block):
            return False
        self.chain.append(block)
        return True
 
    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def to_string(self):
        msg = f"{len(self.chain)} blocks"
        for c in self.chain:
            msg += c.to_string()
        return msg



class BlockchainMiner(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self.blockchain = Blockchain()
        BlockchainNetwork.miners.append(index)
        self.next_nonce = 0
        # the genesis block will be created by "do_some_work"

    def try_mining(self):
        last_block = self.blockchain.last_block

        # I create a block using current timestamp, unconfirmed transactions and nonce
        new_block = Block(index=last_block.index + 1,
                          transactions=self.blockchain.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash,
                          nonce=self.next_nonce)

        # I check if the block passes the proof_of_work test
        proof = self.blockchain.proof_of_work(new_block)
        if proof:
            # if the block is good, I add it to the blockchain, and flush out the unconfirmed transactions
            self.blockchain.add_block(new_block)
            self.blockchain.unconfirmed_transactions = []
            # and I restart nonce from 0. This is not required, it could be set to a random number or whatever
            self.next_nonce = 0
        else:
            # I was not lucky. I change the nonce, since next time I create a block:
            #   I could have no new transactions
            #   I could have the same timestamp since I have a super-fast computer
            # thus the block needs a new nonce to have a change to win the test
            self.next_nonce += 1
        return proof

    def disseminate_chain(self):
        # I send the blockchain to everybody
        for m in BlockchainNetwork.miners:
            if not m == self.index():
                message = BlockchainMessage(self.index(), m, self.blockchain.chain)
                self.medium().send(message)
        # Since I flushed the unconfirmed transactions, I assign the incentives to myself for next block, in case I will be the winner of the proof of work test
        self.blockchain.add_new_transaction(f"(miner {self.index()} gets incentive)")

    def do_some_work(self):
        # if the chain is empty and index == 0, create the genesis block and disseminate the blockchain
        # if index is not 0, do nothing
        if len(self.blockchain.chain) == 0:
            if self.index() == 0:
                self.blockchain.create_genesis_block()
                self.disseminate_chain()
            else:
                return
        # try to mine. If successful, disseminate the chain
        if self.try_mining():
            self.disseminate_chain()

    def run(self):
        # I assign the incentives to myself, in case I add the next block
        self.blockchain.add_new_transaction(f"(miner {self.index()} gets incentive)")
        # since this is a miner, it tries to mine, then it looks for incoming requests (messages) to accumulate transactions etc
        while True:
            self.do_some_work()
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def handle_ingoing(self, ingoing: MessageStub):
        if isinstance(ingoing, BlockchainMessage):
            # TODO: design a logic to respect the "longest chain" rule
            # TODO: implement it
            # HINT: consider what a fork is, that forks can happen, and what to do in that case
            pass
        elif isinstance(ingoing, BlockchainRequestMessage):
            # this is used to send the blockchain data to a client requesting them
            message = BlockchainMessage(self.index(), ingoing.source, self.blockchain.chain)
            self.medium().send(message)
        elif isinstance(ingoing, TransactionMessage):
            self.blockchain.add_new_transaction(ingoing.transaction)
        elif isinstance(ingoing, QuitMessage):
            return False
        return True

    def print_result(self):
        print("Miner " + str(self.index()) + " quits")



class BlockchainClient(Device):
    def __init__(self, index: int, number_of_devices: int, medium: Medium, my_miner: int):
        super().__init__(index, number_of_devices, medium)
        self.my_miner = my_miner

    def run(self):
        # the client spends its time adding transactions (reasonable) and asking how long the blockchain is (unreasonable, but used for the termination)
        self.request_blockchain()
        while True:
            for ingoing in self.medium().receive_all():
                if not self.handle_ingoing(ingoing):
                    return
            self.medium().wait_for_next_round()

    def send_transaction(self):
        message = TransactionMessage(self.index(), self.my_miner, f"(transaction by client {self.index()})")
        self.medium().send(message)

    def request_blockchain(self):
        message = BlockchainRequestMessage(self.index(), self.my_miner)
        self.medium().send(message)

    def handle_ingoing(self, ingoing: MessageStub):
        # the termination clause is *very* random
        # let us say that the client quits when the blockchain is 20 blocks long
        target_len = 20

        if isinstance(ingoing, BlockchainMessage):
            if target_len <= len(ingoing.chain):
                self.medium().send(QuitMessage(self.index(), self.my_miner))
                return False
            # if I don't decide to quit, I add a transaction and request the blockchain data one more time
            self.send_transaction()
            self.request_blockchain()
        return True

    def print_result(self):
        print(f"client {self.index()} quits")



class BlockchainNetwork:
    miners = []
    def __new__(cls, index: int, number_of_devices: int, medium: Medium):
        # first miner MUST have index 0

        if index % 2 == 0:
            return BlockchainMiner(index, number_of_devices, medium)
        else:
            # I associate a miner to each client, in a very aleatory manner
            return BlockchainClient(index, number_of_devices, medium, index-1)



class QuitMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'QUIT REQUEST {self.source} -> {self.destination}'



class BlockchainMessage(MessageStub):
    def __init__(self, sender: int, destination: int, chain: list):
        super().__init__(sender, destination)
        self.chain = chain

    def __str__(self):
        return f'NEW BLOCK MESSAGE {self.source} -> {self.destination}: ({len(self.chain)} blocks)'



class TransactionMessage(MessageStub):
    def __init__(self, sender: int, destination: int, transaction: str):
        super().__init__(sender, destination)
        self.transaction = transaction

    def __str__(self):
        return f'TRANSACTION {self.source} -> {self.destination}: ({self.transaction})'



class BlockchainRequestMessage(MessageStub):
    def __init__(self, sender: int, destination: int):
        super().__init__(sender, destination)

    def __str__(self):
        return f'REQUEST FOR BLOCKCHAIN DATA {self.source} -> {self.destination}'
