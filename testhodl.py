#!/usr/bin/env python3

import grpc
import node_pb2
import node_pb2_grpc
import primitives_pb2
import sys
import random
import string
import time
from enum import Enum
import binascii
import base64

# Get the first command-line argument
# arg1 = sys.argv[1]

server_address = 'localhost:50973'

# Load the client's certificate and key
with open('/tmp/l1-regtest/regtest/client.pem', 'rb') as f:
    client_cert = f.read()
with open('/tmp/l1-regtest/regtest/client-key.pem', 'rb') as f:
    client_key = f.read()

# Load the server's certificate
with open('/tmp/l1-regtest/regtest/server.pem', 'rb') as f:
    server_cert = f.read()

# Create the SSL credentials object
creds = grpc.ssl_channel_credentials(root_certificates=server_cert, private_key=client_key, certificate_chain=client_cert)

# Create the gRPC channel using the SSL credentials
channel = grpc.secure_channel(server_address, creds)

# Create the gRPC stub
stub = node_pb2_grpc.NodeStub(channel)

server_address2 = 'localhost:50974'

# Load the client's certificate and key
with open('/tmp/l2-regtest/regtest/client.pem', 'rb') as f:
    client_cert2 = f.read()
with open('/tmp/l2-regtest/regtest/client-key.pem', 'rb') as f:
    client_key2 = f.read()

# Load the server's certificate
with open('/tmp/l2-regtest/regtest/server.pem', 'rb') as f:
    server_cert2 = f.read()

# Create the SSL credentials object
creds2 = grpc.ssl_channel_credentials(root_certificates=server_cert2, private_key=client_key2, certificate_chain=client_cert2)

# Create the gRPC channel using the SSL credentials
channel2 = grpc.secure_channel(server_address2, creds2)

# Create the gRPC stub
stub2 = node_pb2_grpc.NodeStub(channel2)

# Make the gRPC request
payment_hashes = []
        
class HodlState(Enum):
  OPEN = 0
  SETTLED = 1
  CANCELED = 2
  ACCEPTED = 3


for i in range(100):
    rand_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Make the gRPC request
    request = node_pb2.InvoiceRequest(label=rand_string, amount_msat=primitives_pb2.AmountOrAny(amount=primitives_pb2.Amount(msat=51000000)), description="This payment WILL FREEZE IN YOUR WALLET, check on the website if it was successful. It will automatically return unless you cheat or cancel unilaterally. Payment reference: 9e54963c-81bf-4350-826d-fbbcee052124", cltv=150)

    response = stub.HodlInvoice(request)
    print(binascii.hexlify(response.payment_hash).decode("utf-8"))
    payment_hashes.append(response.payment_hash)
    request2 = node_pb2.PayRequest(bolt11=response.bolt11,
            retry_for=10)

    try: 
        response2 = stub2.Pay.future(request2)
        request3 = node_pb2.HodlInvoiceLookupRequest(payment_hash=binascii.hexlify(response.payment_hash).decode("utf-8").encode())
        while True:
            response3 = stub.HodlInvoiceLookup(request3)
            time.sleep(1)
            if response3.state == HodlState.OPEN.value:
                print("Hodlstate is OPEN")
            elif response3.state == HodlState.CANCELED.value:
                print("Hodlstate is CANCELED")
            elif response3.state == HodlState.SETTLED.value:
                print("Hodlstate is SETTLED")
            elif response3.state == HodlState.ACCEPTED.value:
                print("done paying", i)
                break
            else:
                print("error?")
    except grpc._channel._InactiveRpcError as e:
        status_code = int(e.details().split('code: Some(')[1].split(')')[0])
        error_message = e.details().split('message: "')[1].split('"')[0]
        if status_code == 210:
            print(210)
        else:
            print('Payment failed with error code:', status_code, 'and error message:', error_message)

print("waiting")
time.sleep(60)
for ph in payment_hashes:
    request5 = node_pb2.HodlInvoiceLookupRequest(payment_hash=binascii.hexlify(ph).decode("utf-8").encode())

    response5 = stub.HodlInvoiceLookup(request5)

    if response5.state == HodlState.OPEN.value:
        print("Hodlstate is OPEN")
    elif response5.state == HodlState.CANCELED.value:
        print("Hodlstate is CANCELED")
    elif response5.state == HodlState.SETTLED.value:
        print("Hodlstate is SETTLED")
    elif response5.state == HodlState.ACCEPTED.value:
        print("Hodlstate is ACCEPTED")
        print(response5.htlc_cltv)
    else:
        print("Unknown Hodlstate value: ", response.state)

print("waiting")
time.sleep(60)
for ph in payment_hashes:
    request4 = node_pb2.HodlInvoiceCancelRequest(payment_hash=binascii.hexlify(ph).decode("utf-8").encode())

    response4 = stub.HodlInvoiceCancel(request4)
    # Print the response
    print(response4)
