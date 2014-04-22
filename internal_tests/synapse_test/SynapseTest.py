#
#    ANNarchy-4 NeuralField
#
#
from ANNarchy4 import *
from datetime import datetime

#
# Define the neuron classes
#
Simple = RateNeuron(
    parameters= """   
        tau = 10.0
    """,
    equations = """
        tau * drate/dt +rate = pos(0.3)
    """
)

SimpleSynapse = RateSynapse(
    parameters="""
        tau = 1.0
    """,
    equations = """
        dtest_var/dt = 0.3 - test_var : init = 0.3 
        value = 1.0 / pre.rate : min=-0.5, max=1.0
    """
)

InputPop = Population(name="Input", geometry=(8,1), neuron=Simple)
Layer1Pop = Population(name="Layer1", geometry=(1,1), neuron=Simple)

Proj = Projection(pre="Input", post="Layer1", target='exc', synapse = SimpleSynapse).connect_all_to_all(weights= Uniform(0.0,1.0), delays=2.0)

#
# Analyse and compile everything, initialize the parameters/variables...
#
compile()

import math
import numpy as np

def loop():

    for i in xrange(20):

        if(i==5):
            InputPop.start_record('rate')
        
        if(i==10):
            InputPop.pause_record('rate')
            
        if(i==15):
            InputPop.resume_record('rate')
        
        simulate(1)
    
    rec_rate = InputPop.get_record('rate')
    print 'start', rec_rate['start']
    print 'stop', rec_rate['stop']
    print 'data.shape', rec_rate['data'].shape
    print 'data', rec_rate['data']
    
def loop2():

    to_record = [ {'pop':InputPop, 'var': 'rate'}, {'pop':InputPop, 'var': 'mp'} ]
    
    record(to_record)
    
    for i in xrange(10):
        simulate(1)
    
    rec_data = get_record(to_record)
    for pop in rec_data:
        for var in rec_data[pop]:
            print 'start', rec_data[pop][var]['start']
            print 'stop', rec_data[pop][var]['stop']
            print 'data.shape', rec_data[pop][var]['data'].shape
            print 'data', rec_data[pop][var]['data']
    
def loop3():
    InputPop.start_record('rate')
    InputPop.start_record('mp')
    for i in xrange(15):
        simulate(1)
        #print InputPop.rate
        
    rec_rate = InputPop.get_record('rate')
    for i in xrange(15):
        print 'rate, time',i
        print rec_rate['data'][:,:,i]
        
    rec_mp = InputPop.get_record('mp')
    for i in xrange(15):
        print 'mp, time',i
        print rec_mp['data'][:,:,i]

    #
    # need to re-run to record new data
    InputPop.start_record('rate')
    InputPop.start_record('mp')
    for i in xrange(5):
        simulate(1)
        #print InputPop.rate
        
    rec = InputPop.get_record(['rate', 'mp'])
    for i in xrange(5):
        print 'rate, time',i
        print rec['rate']['data'][:,:,i]
        
        print 'mp, time',i
        print rec['mp']['data'][:,:,i]
       
    #
    # need to re-run to record new data
    InputPop.start_record('rate')
    InputPop.start_record('mp')
    for i in xrange(5):
        simulate(1)

def synapse_test():
    #print 'target:',Proj.dendrite[0].target
    InputPop.baseline = np.ones((8,1))

    #
    #   synapse removal
    print Proj.dendrite(0).rank
    print Proj.dendrite(0).value
    
    print 'test: remove synapse to neuron 1'
    print 'result', Proj.dendrite(0).remove_synapse(1)
    
    print Proj.dendrite(0).rank
    print Proj.dendrite(0).value
    
    #
    #   synapse add - this test should lead to an error output
    print 'remove synapse to neuron 1'    
    Proj.dendrite(0).remove_synapse(1)
    
    #
    #   synapse add - this test should lead to an error output
    print 'add synapse (0, , 0.11111, 0)'    
    Proj.dendrite(0).add_synapse(0, 0.11111, 0)
    
    #
    #   synapse add
    print 'add synapse (1, 0.11111, 0)'        
    Proj.dendrite(0).add_synapse(1, 0.11111, 0)

    print Proj.dendrite(0).rank
    print Proj.dendrite(0).value
    

if __name__ == '__main__':

    set_current_step(10)

    #loop()
    
    #loop2()

    #loop3()
    
    synapse_test()
