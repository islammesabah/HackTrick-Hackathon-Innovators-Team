from code import interact
from gym import Env
from hacktrick_ai_py.agents.agent import Agent, AgentPair
from hacktrick_ai_py.mdp.hacktrick_mdp import HacktrickState, Recipe, HacktrickGridworld
from hacktrick_ai_py.mdp.actions import Action
from hacktrick_rl.rllib.rllib import RlLibAgent, load_agent_pair
from numpy import min_scalar_type

# score = 910
layout = 'final_single'
from queue import PriorityQueue
class Astar:
    def __init__(self):
        global layout
        self.grid = HacktrickGridworld.from_layout_name(layout)
        self.path = []
        self.OPEN = PriorityQueue()
        self.VISITED = []
        self.current_cost = 0
    
    def heuristics_func(self,pos, target):
        x,y = pos[0]-target[0],pos[1]-target[0]
        return abs(x) + abs(y)
    
    def cost_func(self, point,target):
        return self.current_cost + self.heuristics_func(point,target)

    def expand(self,point,agent2_loc,target):
        actions = [(1,0),(-1,0),(0,1),(0,-1)]
        self.current_cost = self.current_cost + 1
        for action in actions:
            new_point = (point[0]+action[0],point[1]+action[1])
            if(new_point == agent2_loc):
                continue
            if(any(new_point in item for item in self.OPEN.queue)):
                continue
            if(new_point in self.VISITED):
                continue
            
            if(self.grid.get_terrain_type_at_pos((new_point[0],new_point[1])) == ' '):
                self.OPEN.put((self.cost_func(new_point,target),new_point))
                continue
            
    def get_path(self,target):
        path = []
        self.VISITED.reverse()
        for item in self.VISITED:
            x,y = target[0]-item[0], target[1]-item[1]
            d = abs(x)+abs(y)
            if(d < 2):
                target = item
                path.append(item)
        path.reverse()
        self.current_cost = 0
        if(len(path)<2):
            return (0,0)
        return (path[1][0]-path[0][0],path[1][1]-path[0][1])

    def search(self,start,end,agent2_loc):
        self.OPEN.put((self.cost_func(start,end),start))
        while not self.OPEN.empty():
            point = self.OPEN.get()[1]
            self.VISITED.append(point)
            if(point == end):
                return self.get_path(end)
            self.expand(point,agent2_loc,end)
            
        return 0



class MainAgent(Agent):

    def __init__(self):
        self.grid = HacktrickGridworld.from_layout_name('final_single')
        self.ingr = []
        self.dict = {}
        self.tick = 0
        self.flag=1
        self.wait = False
        self.obs = False
        self.diclocation = {}
        self.visited = []
        super().__init__()

    def is_on_y(self,target):
        x,_=target
        if(x==0 or x==6):
            return True
        return False

    def next_action(self,pos,target):
        x_t,y_t = target
        x,y=pos[0]-x_t,pos[1]-y_t #check the sign
        if(x==0 and y==0): 
            self.obs = False
            self.visited = []
            return (0,0)
        if(self.is_on_y(target)): #checkthe final orientation of the 
            if(y==0):
                if(self.grid.get_terrain_type_at_pos((pos[0]+int(-x/abs(x)),pos[1])) == ' '):
                    action = (int(-x/abs(x)),0)
                else:
                    self.obs = True
                    if(self.grid.get_terrain_type_at_pos((pos[0],pos[1]-1)) == ' ' and y>0):
                            action = (0,-1)
                    else:
                        action = (0,1)
                    
            else:
                if(self.grid.get_terrain_type_at_pos((pos[0],pos[1] + int(-1*y/abs(y)))) == ' '):
                        action = (0,int(-1*y/abs(y)))
                else:
                    self.obs = True
                    if(self.grid.get_terrain_type_at_pos((pos[0]-1,pos[1])) == ' ' and x>0):
                        action = (-1,0)
                    else:
                        action = (1,0)
        else:
            if(x==0):
                if(self.grid.get_terrain_type_at_pos((pos[0],pos[1] + int(-1*y/abs(y)))) == ' '):
                    action = (0,int(-1*y/abs(y)))
                else:
                    self.obs = True
                    if(self.grid.get_terrain_type_at_pos((pos[0]-1,pos[1])) == ' ' and  x > 0):
                        action = (-1,0)
                    else:
                        action = (1,0)
            else:
                if(self.grid.get_terrain_type_at_pos((pos[0]+int(-x/abs(x)),pos[1])) == ' '):
                    action = (int(-x/abs(x)),0)
                else:
                    self.obs = True
                    if(self.grid.get_terrain_type_at_pos((pos[0],pos[1]-1)) == ' ' and y > 0):
                        action = (0,-1)
                    else:
                        action = (0,1)
        if((pos[0]+action[0],pos[1]+action[1]) in self.visited):
            if(self.grid.get_terrain_type_at_pos((pos[0] - action[0],pos[1]-action[1])) == ' '):
                action = ( -1*action[0], -1*action[1])
            else:
                if(self.grid.get_terrain_type_at_pos((pos[0]+action[1],pos[1]+action[0])) == ' ' ):
                    action = (action[1],action[0])
                else:
                    action = (-1 * action[1], -1 * action[0])
        return action
                    


    def there_obs(self,pos,target):
        while(pos != target):
            action = self.next_action(pos,target)
            if(action == (0,0)): break
            pos = (pos[0]+action[0],pos[1]+action[1])
            if(self.obs == True):
                self.obs = False
                return True
        return False
    
    def better_to_go(self,pos,target):
        best = None
        b = 100
        for t in target:
            x = abs(pos[0]-t[0])+abs(pos[1]-t[1])
            if (best == None):
                best = t
                b = x
            else:
                if(x<b):
                    best = t
                    b = x
        return best



    def make_action(self,pos,target,orient):
        if(target not in self.diclocation):
            x_t,y_t = target

            # Get best location to target
            target_left = (x_t-1,y_t)
            target_right = (x_t+1,y_t)
            target_up = (x_t,y_t-1)
            target_down = (x_t,y_t+1)

            x,y=pos[0]-x_t,pos[1]-y_t #check the sign
            x_l,y_l = pos[0] - target_left[0],pos[1]-target_left[1]
            x_r,y_r = pos[0] - target_right[0],pos[1]-target_right[1]
            x_u,y_u = pos[0] - target_up[0],pos[1]-target_up[1]
            x_d,y_d = pos[0] - target_down[0],pos[1]-target_down[1]
            l_st = abs(x_l)+abs(y_l)
            r_st = abs(x_r)+abs(y_r)
            u_st = abs(x_u)+abs(y_u)
            d_st = abs(x_d)+abs(y_d)
            if((x_l == 0 or y_l ==0) and l_st != 0):
                l_st = l_st + 1
            if((x_r == 0 or y_r ==0) and r_st != 0):
                r_st = r_st + 1
            if((x_u == 0 or y_u ==0) and u_st != 0):
                lust = u_st + 1
            if((x_d == 0 or x_d ==0) and d_st != 0):
                d_st = d_st + 1

            targetlist = list([])
            steps = list([])
            
            if(6>target_left[0]>0 and 6>target_left[1]>0):
                targetlist.append(target_left)
                steps.append(l_st)
            
            if(6>target_right[0]>0 and 6>target_right[1]>0):
                targetlist.append(target_right)
                steps.append(r_st)

            if(6>target_up[0]>0 and 6>target_up[1]>0):
                targetlist.append(target_up)
                steps.append(u_st)

            if(6>target_down[0]>0 and 6>target_down[1]>0):
                targetlist.append(target_down)
                steps.append(d_st)

            new_target = None
            optional_path = None
            while(new_target is None and len(targetlist)!=0):
                min_index = steps.index(min(steps))
                t = targetlist.pop(min_index)
                steps.pop(min_index)
                if(self.grid.get_terrain_type_at_pos(t) == ' '):
                    if(self.there_obs(pos,t)):
                        optional_path = t
                    else:
                        new_target = t

            if(new_target is None): new_target = optional_path

            self.diclocation[target] = new_target

        new_target = self.diclocation[target]
        x_t,y_t = new_target
        x,y=pos[0]-x_t,pos[1]-y_t #check the sign
        if(x==0 and y==0):
            self.visited = []
            self.obs = False
            x_or,y_or = orient
            if(pos[1] == target[1]):
                if(x_or != (target[0]-pos[0])) : 
                    return (target[0]-pos[0],0)
            else:
                if(y_or != (target[1]-pos[1])) : 
                    return (0,target[1]-pos[1])

            return (0,0)
        self.visited.append((pos[0],pos[1]))

        if(pos in self.dict and new_target in self.dict[pos]):
            return self.dict[pos][new_target]
        a = Astar()
        if(pos not in self.dict):
            self.dict[pos] = {}
        self.dict[pos][new_target] = a.search(pos,new_target,(0,0))
        return self.dict[pos][new_target]
  

    def action(self, state):
        if (self.flag == 1) :
            self.ingr = list(state.all_orders[4].ingredients)
            self.ingr.append("construct")
            self.ingr.append("container")
            self.ingr.append("deliver")
            self.flag = 0


        player_position = state.players[0].position
        player_orientation = state.players[0].orientation

        target = 0 
        if(self.ingr[0] == 'projector'):     
            target = self.grid.get_projector_dispenser_locations()[0]
        if(self.ingr[0] == 'laptop'):     
            target = self.grid.get_laptop_dispenser_locations()[0]
        if(self.ingr[0] == 'solar_cell'):     
            target = self.grid.get_solar_cell_dispenser_locations()[0]
        if(self.ingr[0] == 'container'):     
            target = self.better_to_go(player_position,self.grid.get_container_dispenser_locations())
        if(self.ingr[0] == 'deliver'):     
            target = self.grid.get_serving_locations()[0]
        
      
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
    share_agent_logic = True

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