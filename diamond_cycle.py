import json
import time
import contract as c
from datetime import datetime,timedelta
import time
import cloudscraper
import json

dm_contract_addr = "0x3AEDafF8FB09A4109Be8c10CF0c017d3f1F7DcDc"
wallet_public_addr = "0x361472B5784e83fBF779b015f75ea0722741f304"
loop_sleep_seconds = 2
margin_of_error = 0.1
start_polling_threshold_in_seconds = 10

# load private key
wallet_private_key = open('key.txt', "r").readline()

# load abi
f = open('diamond_team_abi.json')
dm_abi = json.load(f)

# create contract
dm_contract = c.connect_to_contract(dm_contract_addr, dm_abi)

# cycle class
class cycleItem: 
    def __init__(self, id, type, minimumBnb): 
        self.id = id 
        self.type = type
        self.minimumBnb = minimumBnb

# cycle types are "reinvest" or "withdraw"
cycle = [] 
cycle.append( cycleItem(1, "reinvest", 0.002) )
cycle.append( cycleItem(2, "reinvest", 0.002) )
cycle.append( cycleItem(3, "reinvest", 0.002) )
cycle.append( cycleItem(4, "reinvest", 0.002) )
cycle.append( cycleItem(5, "reinvest", 0.002) )
cycle.append( cycleItem(6, "reinvest", 0.002) )
cycle.append( cycleItem(7, "reinvest", 0.002) )
nextCycleId = 7

# methods
def reinvest():
    txn = dm_contract.functions.plantSeeds(wallet_public_addr).buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def withdraw():
    txn = dm_contract.functions.sellSeeds().buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def payout_to_reinvest():
    total = dm_contract.functions.payoutToReinvest(wallet_public_addr).call()
    return total/1000000000000000000

def get_user_info():
    return dm_contract.functions.userInfo(wallet_public_addr).call()

def buildTimer(t):
    mins, secs = divmod(int(t), 60)
    hours, mins = divmod(int(mins), 60)
    timer = '{:02d} hours, {:02d} minutes, {:02d} seconds'.format(hours, mins, secs)
    return timer

def countdown(t):
    while t:
        print(f"Next poll in: {buildTimer(t)}", end="\r")
        time.sleep(1)
        t -= 1

def findCycleMinimumBnb(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.minimumBnb
            break
        else:
            x = None

def findCycleType(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.type
            break
        else:
            x = None

def getNextCycleId(currentCycleId):
    cycleLength = len(cycle)
    if currentCycleId == cycleLength:
        return 1
    else:
        return currentCycleId + 1

def seconds_until_cycle():
    time_delta = datetime.combine(
        datetime.now().date() + timedelta(days=1), datetime.strptime("2000", "%H%M").time()
    ) - datetime.now()
    return time_delta.seconds

# create infinate loop that checks contract every set sleep time
nextCycleType = findCycleType(nextCycleId)

def itterate(nextCycleId, nextCycleType):
    cycleMinimumBnb = findCycleMinimumBnb(nextCycleId)
    payoutToReinvest = payout_to_reinvest()
    secondsUntilCycle = seconds_until_cycle()
    userInfo = get_user_info()
    accountValue = userInfo[2]/1000000000000000000

    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%b-%Y (%H:%M:%S)]")

    sleep = loop_sleep_seconds 
    
    print("********** STATS *******")
    print(f"{timestampStr} Next cycle type: {nextCycleType}")
    print(f"{timestampStr} Total value: {accountValue} BNB")
    print(f"{timestampStr} Payout available for reinvest/withdrawal: {payoutToReinvest:.4f}")
    print(f"{timestampStr} Start polling each {(loop_sleep_seconds / 60):.2f} minute {(start_polling_threshold_in_seconds / 60):.3f} minutes before next cycle")
    print("************************")

    if secondsUntilCycle > start_polling_threshold_in_seconds:
        sleep = secondsUntilCycle - start_polling_threshold_in_seconds
            
    if payoutToReinvest >= cycleMinimumBnb:
        if nextCycleType == "reinvest":
            reinvest()
        if nextCycleType == "withdraw":
            withdraw()
        
        if nextCycleType == "reinvest":
            print("********** REINVESTED *******")
            print(f"{timestampStr} Added {payoutToReinvest:.5f} BNB to the pool!")
        if nextCycleType == "withdraw":
            print("********** WITHDREW *********")
            print(f"{timestampStr} Sold {payoutToReinvest:.5f} BNB!")

        nextCycleId = getNextCycleId(nextCycleId)
        nextCycleType = findCycleType(nextCycleId)
        print(f"{timestampStr} Next cycleId is: {nextCycleId}")
        print(f"{timestampStr} Next cycle type will be: {nextCycleType}")
        print("**************************")

    countdown(int(sleep))

retryCount = 0
while True:
    try: 
        if retryCount < 5:
            itterate(nextCycleId, nextCycleType)  
    except Exception as e:
        print("[EXCEPTION] Something went wrong! Message:")
        print(f"[EXCEPTION] {e}")
        retryCount = retryCount + 1
        if retryCount < 5:
            itterate(nextCycleId, nextCycleType)
        print(f"[EXCEPTION] Retrying! (retryCount: {retryCount})")
