#===============================================================================
#
#     Synapse.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2013-2016  Julien Vitay <julien.vitay@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchy is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#===============================================================================
import ANNarchy.core.Global as Global
from ANNarchy.parser.AnalyseSynapse import analyse_synapse

class Synapse(object):
    """
    Base class to define a synapse.
    """
    # Default name and description for reporting
    _default_names = {'rate': "Rate-coded synapse", 'spike': "Spiking synapse"}

    def __init__(self, parameters="", equations="", psp=None, operation='sum', pre_spike=None, post_spike=None, functions=None, pruning=None, creating=None, name=None, description=None, extra_values={} ):
        """ 
        *Parameters*:
        
        * **parameters**: parameters of the neuron and their initial value.
        * **equations**: equations defining the temporal evolution of variables.
        * **psp**: influence of a single synapse on the post-synaptic neuron (default for rate-coded: w*pre.r).
        * **operation**: operation (sum, max, min, mean) performed by the post-synaptic neuron on the individual psp (rate-coded only, default=sum).
        * **pre_spike**: updating of variables when a pre-synaptic spike is received (spiking only).
        * **post_spike**: updating of variables when a post-synaptic spike is emitted (spiking only).
        * **functions**: additional functions used in the equations.
        * **name**: name of the synapse type (used for reporting only).
        * **description**: short description of the synapse type (used for reporting).

        """  
        
        # Store the parameters and equations
        self.parameters = parameters
        self.equations = equations
        self.functions = functions
        self.pre_spike = pre_spike
        self.post_spike = post_spike
        self.psp = psp
        self.operation = operation
        self.extra_values = extra_values
        self.pruning = pruning
        self.creating = creating

        # Type of the synapse TODO: smarter
        self.type = 'spike' if pre_spike else 'rate'

        # Check the operation
        if self.type == 'spike' and self.operation != 'sum':
            Global._error('Spiking synapses can only perform a sum of presynaptic potentials.')

        if not self.operation in ['sum', 'min', 'max', 'mean']:
            Global._error('The only operations permitted are: sum (default), min, max, mean.')

        if (self.pruning or self.creating) and not Global.config['structural_plasticity']:
            Global._error('"structural_plasticity" has not been set to True in setup(), pruning or creating statements in Synapse() would be without effect.')

        # Description
        self.description = None

        # Reporting
        if not hasattr(self, '_instantiated') : # User-defined
            Global._objects['synapses'].append(self)
        elif len(self._instantiated) == 0: # First instantiation of the class
            Global._objects['synapses'].append(self)
        self._rk_synapses_type = len(Global._objects['synapses'])

        if name:
            self.name = name
        else:
            self.name = self._default_names[self.type]

        if description:
            self.short_description = description
        else:
            if self.type == 'spike':
                self.short_description = "User-defined spiking synapse."
            else:
                self.short_description = "User-defined rate-coded synapse."

    def _analyse(self):
        # Analyse the synapse type
        if not self.description:
            self.description = analyse_synapse(self)

    def __add__(self, synapse):  
        Global._error('adding synapse models is not implemented yet.')
              
        #self._variables.update(synapse.variables) 

    def __str__(self):
        import pprint
        return pprint.pformat( self, depth=4 ) #TODO
