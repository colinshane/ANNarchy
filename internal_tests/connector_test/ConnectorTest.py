from ANNarchy4 import *

Simple = RateNeuron(   
parameters="""
    tau = 1.0
    baseline = 0.0
""",
equations="""
    noise = Uniform(0,1)
    tau * dmp / dt + mp = baseline + noise
    rate = pos(mp)
""" 
)

Simple2 = RateSynapse(
psp = """ value * (1.0-pre.rate) """                      
)

In = Population((30, 30), Simple)
Middle = Population((30, 30), Simple)
Out = Population((5, 5), Simple)
 
testOne2One = Projection( 
    pre = In, 
    post = Middle, 
    target = 'one',
)
testOne2One.connect_one_to_one( weights=1.0 )

testAll2All = Projection( 
    pre = Middle, 
    post = Out, 
    target = 'all',
).connect_all_to_all( weights = Uniform(0.0, 1.0), delays = 0.0 )

testGaussian = Projection(
    pre = In, 
    post = Out, 
    target = 'gauss'
).connect_gaussian( sigma=0.7, amp=0.1 )
 
testDog = Projection(
    pre = In, 
    post = Out, 
    target = 'dog', 
).connect_dog(
    amp_pos=0.2, 
    sigma_pos=0.1, 
    amp_neg=0.1, 
    sigma_neg=0.7
)

def stochastic_pattern(pre, post, weight, propability):
    
    synapse_dict = {}
    
    for post_h in xrange(post.height):
        for post_w in xrange(post.width):
            post_rank = post.rank_from_coordinates( (post_w, post_h) )
            
            for pre_h in xrange(pre.height):
                for pre_w in xrange(pre.width):
                    pre_rank = pre.rank_from_coordinates( (pre_w, pre_h) )
                    if np.random.random() < propability:
                        synapse_dict[(pre_rank, post_rank)] = { 'w': weight, 'd': 0.0 }
  
    return synapse_dict
    
testUserPattern = Projection(
    pre = Middle, 
    post = Out, 
    target = 'user' 
).connect_with_func(method=stochastic_pattern, weight=1.0, propability=0.3)   

compile()

visOne2One = Visualization( [ { 'proj': testOne2One, 'var': 'value', 'min': 0.0, 'max': 1.0, 'title': 'weights one2one'} ] )
visOne2One.render()
   
visAll2All = Visualization( [ { 'proj': testAll2All, 'var': 'value', 'min': 0.0, 'max': 1.0, 'title': 'weights all2all'} ] )
visAll2All.render()

visGaussian = Visualization( [ { 'proj': testGaussian, 'var': 'value', 'min': 0.0, 'max': 0.2, 'title': 'weights gaussian'} ] )
visGaussian.render()
 
visDog = Visualization( [ { 'proj': testDog, 'var': 'value', 'min': -0.1, 'max': 0.1, 'title': 'weights difference of gaussian'} ] )
visDog.render()

visTestUserPattern = Visualization( [ { 'proj': testUserPattern, 'var': 'value', 'min': 0.0, 'max': 1.0, 'title': 'user defined pattern'} ] )
visTestUserPattern.render()

raw_input()
