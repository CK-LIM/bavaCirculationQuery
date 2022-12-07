import json
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
from typing import List
from math import *
import requests
from ast import literal_eval
import time
import decimal
import schedule
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import urllib.parse
import logging

start_time = time.time()
# Connect Ethereum node
# avarpc = "https://api.avax.network/ext/bc/C/rpc"
avarpc = "https://rpc.ankr.com/avalanche"
web3 = Web3(Web3.HTTPProvider(avarpc))

print(web3.isConnected())


full_path = os.getcwd()
# Load BAVAABI data
bavaJson = open(full_path+'/abi/'+'Bava.json')
bavaAbi = json.load(bavaJson)

bavaAddress = '0xe19A1684873faB5Fb694CfD06607100A632fF21c'
bavaContract = web3.eth.contract(address=bavaAddress, abi=bavaAbi["abi"])

liquidityAddress = '0xc6c266D553b018aa4CB001FA18Bd0eceff2B5AF9'
airdrop_stakingAddress = '0xe57a7F50De2A71d8805C93786046e1a6B69161F0'
advisorAddress = '0x9a6F4E35a8BF20F207EdAA0876D59e276EeedD3F'
futureTreasuryAddress = '0x355DFe12aF156Ba4C3B010AF973A43304Dd31f5D'
founderAddress = '0x9D834dd94bEd11641d314f2bC7897E99Acd1768D'
teamAddress = '0x7bC1Eb6Ed4d3aB3BEd5EE8b7EeD01dB0714A1Bb1'

print("......")
load_dotenv()
infuraKey = os.getenv("INFURA_KEY")
mongoDBUser = os.getenv("MONGODB_USERNAME")
mongoDBPW = os.getenv("MONGODB_PASSWORD")

# ##########################################################################################################
# Query ERC20 transfer event
# ##########################################################################################################


def queryData():
    latestBlk = web3.eth.blockNumber
    response = requests.get(
        "https://api.coingecko.com/api/v3/simple/price?ids=baklava&vs_currencies=usd")
    responseJson = response.json()
    BAVAPrice = responseJson["baklava"]["usd"]

    maxSupplyData = bavaContract.functions.cap().call(block_identifier='latest')
    totalSupplyData = bavaContract.functions.totalSupply().call(block_identifier='latest')
    locked95BAVAData = bavaContract.functions.lockedSupply().call(
        block_identifier='latest')
    liquidityHeldBAVAData = bavaContract.functions.balanceOf(
        liquidityAddress).call(block_identifier='latest')
    airdrop_stakingHeldBAVAData = bavaContract.functions.balanceOf(
        airdrop_stakingAddress).call(block_identifier='latest')
    advisorHeldBAVAData = bavaContract.functions.balanceOf(
        advisorAddress).call(block_identifier='latest')
    futureTreasuryHeldBAVAData = bavaContract.functions.balanceOf(
        futureTreasuryAddress).call(block_identifier='latest')
    founderHeldBAVAData = bavaContract.functions.balanceOf(
        founderAddress).call(block_identifier='latest')
    teamHeldBAVAData = bavaContract.functions.balanceOf(
        teamAddress).call(block_identifier='latest')

    circulatingSupplyData = totalSupplyData-locked95BAVAData-liquidityHeldBAVAData-airdrop_stakingHeldBAVAData - \
        advisorHeldBAVAData-futureTreasuryHeldBAVAData - \
        founderHeldBAVAData-teamHeldBAVAData

    allData = {
        "last_update_avalanche_block": str(latestBlk),
        "market_price_usd": str(BAVAPrice),
        "decimals": str(18),
        "max_supply": str(maxSupplyData), 
        "total_supply": str(totalSupplyData),
        "circulation": str(circulatingSupplyData),
        "locked_BAVA": str(locked95BAVAData),
        "liquidity_pool_BAVA": str(liquidityHeldBAVAData),
        "airdrop_staking_BAVA": str(airdrop_stakingHeldBAVAData),
        "advisor_BAVA": str(advisorHeldBAVAData),
        "future_treasury_BAVA": str(futureTreasuryHeldBAVAData),
        "founder_BAVA": str(founderHeldBAVAData),
        "team_BAVA": str(teamHeldBAVAData),
        }

# **************************************** Update data ******************************************************

    with open("AllData.json", 'w') as allData_file:
        data = {
            "data": allData}
        json.dump(data, allData_file, indent=4)

##############################################################################################################
# Update and Retreive BDL Total and Past 30 Days Amount from MongoDB
##############################################################################################################


def connectDB():
    # CONNECTION_STRING = "mongodb+srv://"+mongoDBUser+":"+mongoDBPW+"@pundix.ruhha.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    CONNECTION_STRING = "mongodb+srv://"+mongoDBUser+":"+urllib.parse.quote(
        mongoDBPW)+"@cluster0.adqfx.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    # s = MongoClient("mongodb+srv://"+mongoDBUser+":"+urllib.parse.quote(mongoDBPW)+"@cluster0.adqfx.mongodb.net/myFirstDatabase?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    client = MongoClient(CONNECTION_STRING, tls=True,
                         tlsAllowInvalidCertificates=True)
    return client['BAVACirculation']


def updateDB():
    dbName = connectDB()

    collectionName1 = dbName["data"]

    with open("AllData.json") as allData:
        data1 = json.load(allData)
        collectionName1.delete_many({})
        if isinstance(data1, list):
            collectionName1.insert_many(data1)
        else:
            collectionName1.insert_one(data1)

##############################################################################################################
# Read mongo database
##############################################################################################################


def getDB():
    dbName = connectDB()
    collectionName1 = dbName["data"]

    cursor1 = collectionName1.find({})
    for data1 in cursor1:
        data = data1["data"]
        print(data)
# ######################################################################################
# Build flow function
# ######################################################################################


def minCheck():
    try:
        queryData()
        connectDB()
        updateDB()
        print("done query data time: " + str(time.time()))
    except Exception as e:
        print("MinCheck Error happen")
        logging.error(e)

# ######################################################################################
# Build schedule function
# ######################################################################################


def scheduleUpdate():
    schedule.every(1).minutes.do(minCheck)

    while True:
        schedule.run_pending()
        time.sleep(1)

# #############################################################################################################
# Main code
# #############################################################################################################


def main():

    queryData()
    print("done query data time: " + str(time.time()))
    connectDB()
    updateDB()
    getDB()

    print("--- %s seconds ---" % (time.time() - start_time))
    scheduleUpdate()


# __name__ is a built-in variable in Python which evaluates to the name of the current module.
if __name__ == "__main__":
    main()
