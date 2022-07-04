import json
import time
import contract as c
import cyclemanager as cmanager
from datetime import datetime,timedelta
import time
import json

dm_contract_addr = "0x3AEDafF8FB09A4109Be8c10CF0c017d3f1F7DcDc" # this is a proxy contract
# the real code for the proxy is here: https://bscscan.com/address/0xeb8a820edd2327dc3fc6171211ac43cf9dfd191d#code
loop_sleep_seconds = 2
start_polling_threshold_in_seconds = 0

# load private key
wallet_private_key = open('key.txt', "r").readline().strip().strip('\'').strip('\"').strip()

# load public address
wallet_public_addr = open('pa.txt', "r").readline().strip().strip('\'').strip('\"').strip()

# load abi
f = open('diamond_team_abi.json')
dm_abi = json.load(f)

# create contract
dm_contract = c.connect_to_contract(dm_contract_addr, dm_abi)

# create cycle
cycle = cmanager.build_cycle_from_config()

# methods
def reinvest():
    txn = dm_contract.functions.reinvest().buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def withdraw():
    txn = dm_contract.functions.withdraw().buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def get_user_info():
    return dm_contract.functions.userInfo(wallet_public_addr).call()

def daily_payout():
    total = dm_contract.functions.payoutToReinvest(wallet_public_addr).call()
    return total/1000000000000000000

def payout_to_reinvest(userInfo):
    directBonus = userInfo[4]/1000000000000000000
    poolBonus = userInfo[5]/1000000000000000000
    matchBonus = userInfo[6]/1000000000000000000
    dailyPayout = daily_payout()
    return dailyPayout + directBonus + poolBonus + matchBonus

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

def findCycleEndTimerAt(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.endTimerAt
            break
        else:
            x = None

def calcNextCycleId(currentCycleId):
    cycleLength = len(cycle)
    if currentCycleId == cycleLength:
        return 1
    else:
        newCycleId = currentCycleId + 1
        return newCycleId

def seconds_until_cycle(endTimerAt):
    time_delta = datetime.combine(
        datetime.now().date(), datetime.strptime(endTimerAt, "%H:%M").time()
    ) - datetime.now()
    return time_delta.seconds

# create infinate loop that checks contract every set sleep time
nextCycleId = cmanager.getNextCycleId()
nextCycleType = findCycleType(nextCycleId)
retryCount = 0

def itterate():
    global nextCycleId
    global nextCycleType
    cycleMinimumBnb = findCycleMinimumBnb(nextCycleId)
    secondsUntilCycle = seconds_until_cycle(findCycleEndTimerAt(nextCycleId))
    userInfo = get_user_info()
    accountValue = userInfo[2]/1000000000000000000
    payoutToReinvest = payout_to_reinvest(userInfo)

    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%b-%Y (%H:%M:%S)]")

    sleep = loop_sleep_seconds 
    
    print("********** MyDiamondTeam *******")
    print(f"{timestampStr} Next cycle id: {nextCycleId}")
    print(f"{timestampStr} Next cycle type: {nextCycleType}")
    print(f"{timestampStr} Next cycle time: {findCycleEndTimerAt(nextCycleId)}")
    print(f"{timestampStr} Total value: {accountValue:.5f} BNB")
    print(f"{timestampStr} Estimated daily returns: {accountValue*0.015:.8f}")
    print(f"{timestampStr} Payout available for reinvest/withdrawal: {payoutToReinvest:.8f}")
    print(f"{timestampStr} Minimum BNB set for reinvest/withdrawal: {cycleMinimumBnb:.8f}")
    print("************************")

    if secondsUntilCycle > start_polling_threshold_in_seconds:
        sleep = secondsUntilCycle - start_polling_threshold_in_seconds

    countdown(int(sleep))

    userInfo = get_user_info()
    payoutToReinvest = payout_to_reinvest(userInfo)

    if payoutToReinvest >= cycleMinimumBnb:
        if nextCycleType == "reinvest":
            reinvest()
        if nextCycleType == "withdraw":
            withdraw()
        
        if nextCycleType == "reinvest":
            print("********** REINVESTED *******")
            print(f"{timestampStr} Reinvested {payoutToReinvest:.8f} BNB to the pool!")
        if nextCycleType == "withdraw":
            print("********** WITHDREW *********")
            print(f"{timestampStr} Withdrew {payoutToReinvest:.8f} BNB!")

        print("**************************")

        print(f"{timestampStr} Sleeping for 1 min until next cycle starts..")
        countdown(60)

    print("********** IDLE ***********")
    calculatedNextCycleId = calcNextCycleId(nextCycleId)
    cmanager.updateNextCycleId(calculatedNextCycleId)
    nextCycleId = cmanager.getNextCycleId()
    nextCycleType = findCycleType(nextCycleId)
    print(f"{timestampStr} Available reinvest/withdraw did not meet the minimum requirements")
    print(f"{timestampStr} Moving on to next cycle")
    print(f"{timestampStr} Next cycleId is: {nextCycleId}")
    print(f"{timestampStr} Next cycle type will be: {nextCycleType}")
    print("**************************")

 
def run(): 
    global retryCount
    try: 
        itterate()
        run()
    except Exception as e:
        retryCount = retryCount + 1
        print("********* EXCEPTION *****************")
        print("Something went wrong! Message:")
        print(f"{e}")
        if retryCount < 5:
            print(f"[EXCEPTION] Retrying! (retryCount: {retryCount})")
            print("*************************************")
            run()
        else:
            print("********* TERMINATING *****************")
            print("Exception occurred 5 times. Terminating!")

run()
