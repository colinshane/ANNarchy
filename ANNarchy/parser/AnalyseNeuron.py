"""

    AnalyseNeuron.py

    This file is part of ANNarchy.

    Copyright (C) 2013-2016  Julien Vitay <julien.vitay@gmail.com>,
    Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ANNarchy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
from ANNarchy.core.Global import _error, _warning, config
from ANNarchy.core.Random import available_distributions, distributions_arguments, distributions_equivalents
from ANNarchy.parser.Equation import Equation
from ANNarchy.parser.StringManipulation import *
from ANNarchy.parser.ITE import *
from ANNarchy.parser.Extraction import *
from ANNarchy.parser.CoupledEquations import CoupledEquations

def analyse_neuron(neuron):
    """ 
    Parses the structure and generates code snippets for the neuron type.

    It returns a ``description`` dictionary with the following fields:

    * 'object': 'neuron' by default, to distinguish it from 'synapse'
    * 'type': either 'rate' or 'spiking'
    * 'raw_parameters': provided field
    * 'raw_equations': provided field
    * 'raw_functions': provided field
    * 'raw_reset': provided field
    * 'raw_spike': provided field
    * 'refractory': provided field
    * 'parameters': list of parameters defined for the neuron type
    * 'variables': list of variables defined for the neuron type
    * 'functions': list of functions defined for the neuron type
    * 'attributes': list of names of all parameters and variables
    * 'local': list of names of parameters and variables which are local to each neuron
    * 'global': list of names of parameters and variables which are global to the population
    * 'targets': list of targets used in the equations
    * 'random_distributions': list of random number generators used in the neuron equations
    * 'global_operations': list of global operations (min/max/mean...) used in the equations (unused)
    * 'spike': when defined, contains the equations of the spike conditions and reset.

    Each parameter is a dictionary with the following elements:

    * 'bounds': unused
    * 'ctype': 'type of the parameter: 'double', 'int' or 'bool'
    * 'eq': original equation in text format
    * 'flags': list of flags provided after the :
    * 'init': initial value
    * 'locality': 'local' or 'global'
    * 'name': name of the parameter

    Each variable is a dictionary with the following elements:
    
    * 'bounds': dictionary of bounds ('init', 'min', 'max') provided after the :
    * 'cpp': C++ code snippet updating the variable
    * 'ctype': type of the variable: 'double', 'int' or 'bool'
    * 'dependencies': list of variable and parameter names on which the equation depends
    * 'eq': original equation in text format
    * 'flags': list of flags provided after the :
    * 'init': initial value
    * 'locality': 'local' or 'global'
    * 'method': numericalmethod for ODEs
    * 'name': name of the variable
    * 'switch': ODEs have a switch term
    * 'transformed_eq': same as eq, except special terms (sums, rds) are replaced with a temporary name
    * 'untouched': dictionary of special terms, with their new name as keys and replacement values as values.

    The 'spike' element (when present) is a dictionary containing:

    * 'spike_cond': the C++ code snippet containing the spike condition ("v%(local_index)s > v_T")
    * 'spike_cond_dependencies': list of variables/parameters on which the spike condition depends
    * 'spike_reset': a list of reset statements, each of them composed of :
        * 'constraint': either '' or 'unless_refractory'
        * 'cpp': C++ code snippet
        * 'dependencies': list of variables on which the reset statement depends
        * 'eq': original equation in text format
        * 'name': name of the reset variable

    """

    # Store basic information
    description = {
        'object': 'neuron',
        'type': neuron.type,
        'raw_parameters': neuron.parameters,
        'raw_equations': neuron.equations,
        'raw_functions': neuron.functions,
    }

    # Spiking neurons additionally store the spike condition, the reset statements and a rrefarctory period
    if neuron.type == 'spike': 
        description['raw_reset'] = neuron.reset
        description['raw_spike'] = neuron.spike
        description['refractory'] = neuron.refractory

    # Extract parameters and variables names
    parameters = extract_parameters(neuron.parameters, neuron.extra_values)
    variables = extract_variables(neuron.equations)
    description['parameters'] = parameters
    description['variables'] = variables

    # Make sure r is defined for rate-coded networks
    if neuron.type == 'rate':
        for var in description['parameters'] + description['variables']:
            if var['name'] == 'r':
                break
        else:
            _error('Rate-coded neurons must define the variable "r".')

    else: # spiking neurons define r by default, it contains the average FR if enabled
        for var in description['parameters'] + description['variables']:
            if var['name'] == 'r':
                _error('Spiking neurons use the variable "r" for the average FR, use another name.')

        description['variables'].append(
            {
                'name': 'r', 'locality': 'local', 'bounds': {}, 'ctype': 'double', 'init': 0.0,
                'flags': [], 'eq': '', 'cpp': ""
            }
        )

    # Extract functions
    functions = extract_functions(neuron.functions, False)
    description['functions'] = functions

    # Build lists of all attributes (param + var), which are local or global
    attributes, local_var, global_var = get_attributes(parameters, variables)

    # Test if attributes are declared only once
    if len(attributes) != len(list(set(attributes))):
        _error('Attributes must be declared only once.', attributes)

    # Store the attributes
    description['attributes'] = attributes
    description['local'] = local_var
    description['global'] = global_var

    # Extract all targets
    targets = extract_targets(variables)
    description['targets'] = targets
    if neuron.type == 'spike': # Add a default reset behaviour for conductances
        for target in targets:
            found = False
            for var in description['variables']:
                if var['name'] == 'g_' + target:
                    found = True
                    break
            if not found:
                description['variables'].append(
                    { 
                        'name': 'g_'+target, 'locality': 'local', 'bounds': {}, 'ctype': 'double',
                        'init': 0.0, 'flags': [], 'eq': 'g_' + target+ ' = 0.0'
                    }
                )
                description['attributes'].append('g_'+target)
                description['local'].append('g_'+target)

    # Extract RandomDistribution objects
    random_distributions = extract_randomdist(description)
    description['random_distributions'] = random_distributions

    # Extract the spike condition if any
    if neuron.type == 'spike':
        description['spike'] = extract_spike_variable(description)

    # Global operation TODO
    description['global_operations'] = []

    # The ODEs may be interdependent (implicit, midpoint), so they need to be passed explicitely to CoupledEquations
    concurrent_odes = []

    # Translate the equations to C++
    for variable in description['variables']:
        # Get the equation
        eq = variable['transformed_eq']
        if eq.strip() == "":
            continue

        # Special variables (sums, global operations, rd) are placed in untouched, so that Sympy ignores them
        untouched={}

        # Replace sum(target) with pop%(id)s.sum_exc[i]
        for target in description['targets']:
            eq = re.sub('sum\(\s*'+target+'\s*\)', '__sum_'+target+'__', eq)
            untouched['__sum_'+target+'__'] = '_sum_' + target + '%(local_index)s'

        # Extract global operations
        eq, untouched_globs, global_ops = extract_globalops_neuron(variable['name'], eq, description)

        # Add the untouched variables to the global list
        for name, val in untouched_globs.items():
            if not name in untouched.keys():
                untouched[name] = val
        description['global_operations'] += global_ops

        # Extract if-then-else statements
        eq, condition = extract_ite(variable['name'], eq, description)

        # Find the numerical method if any
        method = find_method(variable)

        # Process the bounds
        if 'min' in variable['bounds'].keys():
            if isinstance(variable['bounds']['min'], str):
                translator = Equation(
                    variable['name'],
                    variable['bounds']['min'],
                    description,
                    type = 'return',
                    untouched = untouched
                )
                variable['bounds']['min'] = translator.parse().replace(';', '')

        if 'max' in variable['bounds'].keys():
            if isinstance(variable['bounds']['max'], str):
                translator = Equation(
                    variable['name'],
                    variable['bounds']['max'],
                    description,
                    type = 'return',
                    untouched = untouched
                )
                variable['bounds']['max'] = translator.parse().replace(';', '')

        # Analyse the equation
        if condition == []:# No if-then-else
            translator = Equation(
                variable['name'],
                eq,
                description,
                method = method,
                untouched = untouched
            )
            code = translator.parse()
            dependencies = translator.dependencies()
        else: # An if-then-else statement
            code, dependencies = translate_ITE(
                        variable['name'],
                        eq,
                        condition,
                        description,
                        untouched )

        # ODEs have a switch statement:
        #   double _r = (1.0 - r)/tau;
        #   r[i] += dt* _r;
        # while direct assignments are one-liners:
        #   r[i] = 1.0
        if isinstance(code, str):
            cpp_eq = code
            switch = None
        else: # ODE
            cpp_eq = code[0]
            switch = code[1]

        # Replace untouched variables with their original name
        for prev, new in untouched.items():
            if prev.startswith('g_'):
                cpp_eq = re.sub(r'([^_]+)'+prev, r'\1'+new, ' ' + cpp_eq).strip()
                if switch:
                    switch = re.sub(r'([^_]+)'+prev, new, ' ' + switch).strip()
            else:
                cpp_eq = re.sub(prev, new, cpp_eq)
                if switch:
                    switch = re.sub(prev, new, switch)

        # Replace local functions
        for f in description['functions']:
            cpp_eq = re.sub(r'([^\w]*)'+f['name']+'\(', r'\1'+f['name'] + '(', ' ' + cpp_eq).strip()

        # Store the result
        variable['cpp'] = cpp_eq # the C++ equation
        variable['switch'] = switch # switch value of ODE
        variable['untouched'] = untouched # may be needed later
        variable['method'] = method # may be needed later
        variable['dependencies'] = dependencies # may be needed later

        # If the method is implicit or midpoint, the equations must be solved concurrently (depend on v[t+1])
        if method in ['implicit', 'midpoint']:
            concurrent_odes.append(variable)

    # After all variables are processed, do it again if they are concurrent
    if len(concurrent_odes) > 1 :
        solver = CoupledEquations(description, concurrent_odes)
        new_eqs = solver.process_variables()
        for idx, variable in enumerate(description['variables']):
            for new_eq in new_eqs:
                if variable['name'] == new_eq['name']:
                    description['variables'][idx] = new_eq

    return description