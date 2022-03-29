from code import interact
from gym import Env
from hacktrick_ai_py.agents.agent import Agent, AgentPair
from hacktrick_ai_py.mdp.hacktrick_mdp import HacktrickState, Recipe, HacktrickGridworld
from hacktrick_ai_py.mdp.actions import Action
from hacktrick_rl.rllib.rllib import RlLibAgent, load_agent_pair

# score = 1120
class MainAgent(Agent):

    def __init__(self):
        self.grid = HacktrickGridworld.from_layout_name('round_of_16_collaborative')
        self.ingr = []
        self.tick = 0
        self.flag=1
        self.wait = False
        super().__init__()

    def is_on_y(self,target):
        x,_=target
        if(x==0 or x==6):
            return True
        return False

    def make_action(self,pos,target,orient):

        x_t,y_t = target
        if(x_t == 0): x_t=1
        elif(x_t == 6): x_t=5
        elif(y_t == 0): y_t=1
        elif(y_t == 6): y_t=5
        else:y_t = y_t-1
        x,y=pos[0]-x_t,pos[1]-y_t #check the sign

        if(x==0 and y==0):
            x_or,y_or = orient
            if(y_t == 5 and y_or != 1) : return (0,1)
            if(y_t == 1 and y_or != -1) : return (0,-1)
            # if(x_t == 5 and x_or != 1) : return (1,0)
            # if(x_t == 1 and x_or != -1) : return (-1,0)
            return (0,0)

        if(self.is_on_y(target)): #checkthe final orientation of the 
            if(y==0):
                return (int(-x/abs(x)),0)
            else:
                return (0,int(-1*y/abs(y)))
        else:
            if(x==0):
                return (0,int(-1*y/abs(y)))
            else:
                return (int(-x/abs(x)),0)

    def action(self, state):
        if (self.flag == 1) :
            self.ingr = list(state.all_orders[4].ingredients)
            self.ingr.append("construct")
            self.ingr.append("container")
            self.ingr.append("deliver")
            self.flag = 0

        target = 0 
        if(self.ingr[0] == 'projector'):     
            target = self.grid.get_projector_dispenser_locations()[0]
        if(self.ingr[0] == 'laptop'):     
            target = self.grid.get_laptop_dispenser_locations()[0]
        if(self.ingr[0] == 'solar_cell'):     
            target = self.grid.get_solar_cell_dispenser_locations()[0]
        if(self.ingr[0] == 'container'):     
            target = self.grid.get_container_dispenser_locations()[0]
        if(self.ingr[0] == 'deliver'):     
            target = self.grid.get_serving_locations()[0]
        
        player_position = state.players[0].position
        player_orientation = state.players[0].orientation
        
      
        if(self.ingr[0] == 'deliver' and self.wait):
            obj = list(state.objects.values())
            if(len(obj) > 0 and obj[0].is_cooking):
                action = (0,0)
            else:
                action = 'interact'
                self.wait = False
        elif(self.ingr[0] == 'construct'):
            action = 'interact'
            self.ingr.append(self.ingr.pop(0))
        elif state.players[0].held_object is None:#not holding
           action1 = self.make_action(player_position,target,player_orientation)
           if action1 == (0,0):
               action = 'interact'
           else:
               action = action1
        else:
            if(self.ingr[0] == 'deliver'):
                action1 = self.make_action(player_position,target,player_orientation)
            else:
                action1 = self.make_action(player_position,self.grid.get_construction_site_locations()[0],player_orientation)

            if action1 == (0,0):
                if(self.ingr[0]=='container'):
                    self.wait = True
                action = 'interact'
                self.ingr.append(self.ingr.pop(0))
            else:
                action = action1
            
        
        action_probs = {}
        return action, action_probs


class OptionalAgent(Agent):
    
    def __init__(self):
        super().__init__()
        
    def action(self, state):
        # Implement your logic here
        action, action_probs = Action.STAY, {}
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