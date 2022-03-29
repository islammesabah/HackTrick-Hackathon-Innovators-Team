from code import interact
from gym import Env
from hacktrick_ai_py.agents.agent import Agent, AgentPair
from hacktrick_ai_py.mdp.hacktrick_mdp import HacktrickState, Recipe, HacktrickGridworld
from hacktrick_ai_py.mdp.actions import Action
from hacktrick_rl.rllib.rllib import RlLibAgent, load_agent_pair



def is_on_y(target):
    x,_=target
    if(x==0 or x==6):
        return True
    return False



flag = 1
ingr = []
last_trans = False
last_pos_1 = (0,0)
last_orien_2 = (0,0)
last_action_1 = (0,0)
last_pos_2 = (0,0)
last_orien_2 = (0,0)
last_action_2 = (0,0)

agent_0 = 0
agent_1 = 1
wait = True
construct = False
finish = False
agent_1_const = False
agent_0_const = False

def make_action(pos,target,orient):
    x_t,y_t = target
    if(x_t == 0): x_t=1
    if(x_t == 6): x_t=5
    if(y_t == 0): y_t=1
    if(y_t == 6): y_t=5
    x,y=pos[0]-x_t,pos[1]-y_t #check the sign
    if(x==0 and y==0):
        x_or,y_or = orient
        if(y_t == 5 and y_or != 1) : return (0,1)
        if(y_t == 1 and y_or != -1) : return (0,-1)
        return (0,0)
    global last_trans
    last_trans = True
    if(is_on_y(target)): #checkthe final orientation of the 
        if(y==0):
          return (int(-x/abs(x)),0)
        else:
         return (0,int(-1*y/abs(y)))
    else:
        if(x==0):
          return (0,int(-1*y/abs(y)))
        else:
          return (int(-x/abs(x)),0)

def make_action_if_stuck(pos_1,pos_2,action_1,action_2):
    x_1, y_1 = pos_1
    x_2, y_2 = pos_2
    x_a_1, y_a_1 = action_1
    x_a_2, y_a_2 = action_2

    new_pos_1_x = x_1+x_a_1
    new_pos_1_y = y_1+y_a_1
    new_pos_2_x = x_2+x_a_2
    new_pos_2_y = y_2+y_a_2

    X = False
    if(new_pos_1_x == new_pos_2_x and new_pos_1_y == new_pos_2_y): X = True
    if ((new_pos_1_x == x_2 and new_pos_1_y == y_2) and (new_pos_2_x == x_1 and new_pos_2_y ==y_1)): X= True
    if (X):
        if(y_1 == y_2):
                if(y_2 > 1):
                    return action_1,(0,-1)
                else:
                    return action_1,(0,1)
        if(x_1 == x_2):
                if(x_2 > 1 ):
                    return action_1,(-1,0)
                else:
                    return action_1, (1,0)

        return(action_1,(0,0))
    return action_1,action_2
    
    

class MainAgent(Agent):

    def __init__(self):
        self.grid = HacktrickGridworld.from_layout_name('leaderboard_collaborative')
        self.tick = 0
        super().__init__()

    def action(self, state):
        global flag
        global ingr
        global last_trans
        global last_action_1
        global last_pos_1
        global last_action_2
        global last_pos_2
        global last_orien_1
        global agent_0
        global agent_1
        global construct
        global wait
        global agent_0_const
        action_probs = {}
        if (flag == 1) :
            ingr = list(['laptop','solar_cell','laptop','solar_cell','projector'])
            ingr.append("container")
            ingr.append("deliver")
            flag = 0

        target = 0 
        if(ingr[agent_0] == 'projector'):     
            target = self.grid.get_projector_dispenser_locations()[0]
        if(ingr[agent_0] == 'laptop'):     
            target = self.grid.get_laptop_dispenser_locations()[0]
        if(ingr[agent_0] == 'solar_cell'):     
            target = self.grid.get_solar_cell_dispenser_locations()[0]
        if(ingr[agent_0] == 'container'):     
            target = self.grid.get_container_dispenser_locations()[0]
        if(ingr[agent_0] == 'deliver'):     
            target = self.grid.get_serving_locations()[0]
        
        player_position = state.players[0].position
        player_orientation = state.players[0].orientation

        if(agent_0_const):
            action = 'interact'
            construct = True
            last_trans = False
            agent_0_const = False

        elif(ingr[agent_0] == 'deliver' and wait):
            obj = list(state.objects.values())
            if(len(obj) > 0 and obj[0].is_cooking):
                action = (0,0)
                last_trans = False
            else:
                action = 'interact'
                construct = False
                last_trans = False
                wait = False

        elif state.players[0].held_object is None:#not holding
           action1 = make_action(player_position,target,player_orientation)
           if action1 == (0,0):
               action = 'interact'
               last_trans = False
           else:
               action = action1
               last_trans = True
        else:
            if(ingr[agent_0] == 'deliver'):
                action1 = make_action(player_position,target,player_orientation)
            else:
                action1 = make_action(player_position,(3,0),player_orientation)
            
            if(construct and agent_0 < len(ingr)-2):
                action = make_action(player_position,(2,0),player_orientation)    
                last_trans = True
            elif action1 == (0,0):
                if(agent_0 == len(ingr)-3 or agent_0 == len(ingr)-4):
                    action = 'interact'
                    last_trans = False
                    agent_0 = len(ingr)-2
                    if(agent_1 >= len(ingr)-2):
                        agent_0 = 0
                        agent_0_const = True
                elif(ingr[agent_0] == 'container' and not(construct)):
                    action = make_action(player_position,(2,0),player_orientation)
                    last_trans = True
                else:
                    action = 'interact'
                    last_trans = False
                    if(ingr[agent_0] == 'deliver'):
                        agent_0 = 1
                    else:
                        if(agent_0 == len(ingr)-2):
                            wait = True
                            agent_0 = agent_0 + 1
                        elif agent_0 == len(ingr)-1:
                            agent_0 = 1
                        else:
                            agent_0 = (agent_0 + 2) % len(ingr)
            else:
                action = action1
                last_trans = True
    
        last_pos_1 = player_position
        last_action_1 = action
        last_orien_1 = player_orientation
        return action, action_probs



class OptionalAgent(Agent):
    
    def __init__(self):
        self.grid = HacktrickGridworld.from_layout_name('leaderboard_collaborative')
        self.tick = 0
        super().__init__()
        
    def action(self, state):
        global flag
        global ingr
        global last_trans
        global last_action_1
        global last_pos_1
        global last_orien_2
        global last_action_2
        global last_pos_2
        global agent_0
        global agent_1
        global construct
        global wait
        global last_pos
        global agent_1_const
        action_probs = {}
        
        target = 0 
        if(ingr[agent_1] == 'projector'):     
            target = self.grid.get_projector_dispenser_locations()[0]
        if(ingr[agent_1] == 'laptop'):     
            target = self.grid.get_laptop_dispenser_locations()[0]
        if(ingr[agent_1] == 'solar_cell'):     
            target = self.grid.get_solar_cell_dispenser_locations()[0]
        if(ingr[agent_1] == 'container'):     
            target = self.grid.get_container_dispenser_locations()[0]
        if(ingr[agent_1] == 'deliver'):     
            target = self.grid.get_serving_locations()[0]
        
        player_position = state.players[1].position
        player_orientation = state.players[1].orientation

       
        if(agent_1_const):
            action = 'interact'
            construct = True
            agent_1_const = False
        elif(ingr[agent_1] == 'deliver' and wait):
            obj = list(state.objects.values())
            if(len(obj) > 0 and obj[0].is_cooking):
                action = (0,0)
            else:
                action = 'interact'
                construct = False
                last_trans = False
                wait = False

        elif state.players[1].held_object is None:#not holding
           action1 = make_action(player_position,target,player_orientation)
           if action1 == (0,0):
               action = 'interact'
               last_trans = False
           else:
               action = action1
               last_trans = True
        else:
            if(ingr[agent_1] == 'deliver'):
                action1 = make_action(player_position,target,player_orientation)
            else:
                action1 = make_action(player_position,(3,0),player_orientation)

            if(construct and agent_1 < len(ingr)-2):
                action = make_action(player_position,(2,0),player_orientation)    
                last_trans = True
            elif action1 == (0,0):
                if(agent_1 == len(ingr)-3 or agent_1 == len(ingr)-4):
                    action = 'interact'
                    last_trans = False
                    agent_1 = len(ingr)-2
                    if(agent_0 >= len(ingr)-2):
                        agent_1 = 0
                        agent_1_const = True
                elif(ingr[agent_1] == 'container' and not(construct)):
                    action = make_action(player_position,(2,0),player_orientation)
                else:
                    action = 'interact'
                    last_trans = False
                    if(ingr[agent_1] == 'deliver'):
                        agent_1 = 1
                    else:
                        if(agent_1 == len(ingr)-2):
                            wait = True
                            agent_1 = agent_1 + 1
                        elif agent_1 == len(ingr)-1:
                            agent_1 = 1
                        else:
                            agent_1 = (agent_1 + 2) % len(ingr)
            else:
                action = action1
                last_trans = True

        if(action != 'interact' and last_action_1 != 'interact'):
            _,action = make_action_if_stuck(last_pos_1,player_position,last_action_1,action)
        last_pos_2 = player_position
        last_action_2 = action    
        last_orien_2 = player_orientation
        return action, action_probs

class HacktrickAgent(object):    # Enable this flag if you are using reinforcement learning from the included ppo ray support library
    RL = False
    # Rplace with the directory for the trained agent
    # Note that `agent_dir` is the full path to the checkpoint FILE, not the checkpoint directory
    agent_dir = ''
    # If you do not plan to use the same agent logic for both agents and use the OptionalAgent set it to False
    # Does not matter if you are using RL as this is controlled by the RL agent
    share_agent_logic = False

    def __init__(self):
        Recipe.configure({})
        if self.RL:
            agent_pair = load_agent_pair(self.agent_dir)
            self.agent0 = agent_pair.a0
            self.agent1 = agent_pair.a1
        else:
            self.agent0 = MainAgent()
            self.agent1 = OptionalAgent()
    
    def set_mode(self, mode):
        self.mode = mode

        if "collaborative" in self.mode:
            if self.share_agent_logic and not self.RL:
                self.agent1 = MainAgent()
            self.agent_pair = AgentPair(self.agent0, self.agent1)
        else:
            self.agent1 =None
            self.agent_pair =None
    
    def map_action(self, action):
        action_map = {(0, 0): 'STAY', (0, -1): 'UP', (0, 1): 'DOWN', (1, 0): 'RIGHT', (-1, 0): 'LEFT', 'interact': 'SPACE'}
        action_str = action_map[action[0]]
        return action_str

    def action(self, state_dict):
        state = HacktrickState.from_dict(state_dict['state']['state'])

        if "collaborative" in self.mode:
            (action0, action1) = self.agent_pair.joint_action(state)
            action0 = self.map_action(action0)
            action1 = self.map_action(action1)
            action = [action0, action1]
        else:
            action0 = self.agent0.action(state)
            action0 = self.map_action(action0)
            action = action0

        return action