"""
IO.py
"""
from ANNarchy4.core import Global 
import os
import cPickle

def save(in_file, pure_data=True, variables=True, connections=True):
    """
    Save the current network state
    
    Parameter:
    
    * *in_file*: filename
    * *pure_data*: if True only the network state will be saved. If False additionaly all neuron and synapse definitions will be saved (by default True).
    * *variables*: if True population data will be saved (by default True)
    * *connections*: if True projection data will be saved (by default True)
    """    
    # Check if the repertory exist
    (path, filename) = os.path.split(in_file) 
    
    if not path == '':
        if not os.path.isdir(path):
            print 'creating folder', path
            os.mkdir(path)
    
    #
    #
    if pure_data:
        data = _net_description(variables, connections)
    else:
        #
        # steps_
        #
        # pickle neuron, synapse
        #
        # pickle proj, population
        #
        # data = above + _description_data(variables, connections)
        print 'Complete save currently not implemented'
        return
    
    #
    # save in Pythons pickle format
    with open(in_file, mode = 'w') as w_file:
        try:
            cPickle.dump(data, w_file, protocol=cPickle.HIGHEST_PROTOCOL)
        except Exception, e:
            print 'Error while saving in Python pickle format.'
            print e
            return

def load(in_file, pure_data=True):
    """
    Load the current network state.
    
    Parameter:
    
    * *in_file*: filename
    * *pure_data*: if True only the network state will be loaded assumes that the network is build up. If False the stored neuron and synapse definitions will be used to build up a network (by default True).
    * *variables*: if True population data will be saved (by default True)
    * *connections*: if True projection data will be saved (by default True)
    """    
    with open(in_file, mode = 'r') as r_file:
        try:
            net_desc = cPickle.load(r_file)
    
            if pure_data:
                _load_pop_data(net_desc)
                
                _load_proj_data(net_desc)
            else:
                #
                # steps_
                #
                # unpickle neuron, synapse
                #
                # unpickle proj, population
                #
                # compile()
                #
                # _load_only_data(net_desc)
                print 'Load network from scratch is not implemented yet.'
                return
    
        except Exception, e:
            print 'Error while loading in Python pickle format.'
            print e
            return
  
def _net_description(variables, connections):
    """
    Returns a dictionary containing the requested network data.
    
    Parameter:
    
        * *variables*: if *True* the population data will be saved
        * *projection*: if *True* the projection data will be saved
    """
    network_desc = {}
    
    if variables:
        for pop in Global._populations:
            pop_desc = {}
            pop_desc['name'] = pop.name
    
            varias = {}
            for var in pop.variables:
                varias[var] = pop.get_variable(var)
            pop_desc['variables'] = varias
                
            params = {}
            for par in pop.parameters:
                params[par] = pop.get_parameter(par)
            pop_desc['parameter'] = params
            
            network_desc[pop.name] = pop_desc 

    if connections:
        for proj in Global._projections:
    
            proj_desc = {}
            proj_desc['post_ranks'] = proj._post_ranks
                  
            dendrites = []  
            for dendrite in proj.dendrites:
                dendrite_desc = {}
        
                dendrite_desc['post_rank'] = dendrite.post_rank
                
                varias = {}
                for var in dendrite.variables:
                    varias[var] = dendrite.get_variable(var)
                dendrite_desc['variables'] = varias
                    
                params = {}
                for par in dendrite.parameters:
                    params[par] = dendrite.get_parameter(par)
                dendrite_desc['parameter'] = params
                
                dendrites.append(dendrite_desc)
            
            proj_desc['dendrites'] = dendrites
            network_desc[proj.name] = proj_desc 

    return network_desc
            
def _load_pop_data(net_desc):
    """
    Update populations with the stored data set. 
    """
    #
    # over all popolations
    for pop in Global._populations:
        
        # check if the population is contained in save file
        if pop.name in net_desc.keys():
            pop_desc = net_desc[pop.name]
            
            for var in pop_desc['variables'].keys():
                exec("pop."+var+" = pop_desc['variables']['"+var+"'].reshape(pop.size)")
                
            for par in pop_desc['parameter'].keys():
                exec("pop."+par+" = pop_desc['parameter']['"+par+"']")
    
def _load_proj_data(net_desc):
    """
    Update projections with the stored data set. 
    """
    for net_proj in Global._projections:

        if net_proj.name in net_desc.keys():
            
            proj_desc = net_desc[net_proj.name]
            
            #
            # over all stored dendrites
            for saved_dendrite in proj_desc['dendrites']:
                
                net_dendrite = net_proj.dendrite_by_rank(saved_dendrite['post_rank'])
                
                for var in saved_dendrite['variables'].keys():
                    exec("net_dendrite."+var+" = saved_dendrite['variables']['"+var+"'].reshape(net_proj.pre.size)")
                    
                for par in saved_dendrite['parameter'].keys():
                    exec("net_dendrite."+par+" = saved_dendrite['parameter']['"+par+"']")
                    