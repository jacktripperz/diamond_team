import json
# cycle types are "reinvest" or "withdraw"

class Iteration: 
    def __init__(self, id, type, endTimerAt, minimumBnb): 
        self.id = id 
        self.type = type
        self.endTimerAt = endTimerAt
        self.minimumBnb = minimumBnb

def build_cycle_from_config():
    cycle = []
    cycle_file = open('cycle_config.json')
    cycle_json = json.load(cycle_file)
    for iteration in cycle_json:
        iterationClass = Iteration(**iteration)
        cycle.append(iterationClass)
    return cycle
