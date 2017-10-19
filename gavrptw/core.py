# -*- coding: utf-8 -*-

import os
import random
from json import load
from csv import DictWriter
from deap import base, creator, tools
from . import BASE_DIR
from utils import makeDirsForFile, exist


def ind2route(individual, instance):
    route = []
    routeWithTwoResources = []
    vehicleCapacity = instance['vehicle_capacity']
    lightVehicleCapcity = instance['light_vehicle_capacity']
    lightVehicleRange = instance['light_vehicle_range']
    deportDueTime =  instance['deport']['due_time']
    # Initialize a sub-route
    subRoute = []
    vehicleLoad = 0
    elapsedTime = 0
    lastCustomerID = 0
    for customerID in individual:
        # Update vehicle load
        demand = instance['customer_%d' % customerID]['demand']
        updatedVehicleLoad = vehicleLoad + demand
        # Update elapsed time
        serviceTime = instance['customer_%d' % customerID]['service_time']
        returnTime = instance['distance_matrix'][customerID][0]
        updatedElapsedTime = elapsedTime + instance['distance_matrix'][lastCustomerID][customerID] + serviceTime + returnTime
        # Validate vehicle load and elapsed time
        if (updatedVehicleLoad <= vehicleCapacity) and (updatedElapsedTime <= deportDueTime):
            # Add to current sub-route
            subRoute.append(customerID)
            vehicleLoad = updatedVehicleLoad
            elapsedTime = updatedElapsedTime - returnTime
        else:
            # Save current sub-route
            route.append(subRoute)
            # Initialize a new sub-route and add to it
            subRoute = [customerID]
            vehicleLoad = demand
            elapsedTime = instance['distance_matrix'][0][customerID] + serviceTime
        # Update last customer ID
        lastCustomerID = customerID
    if subRoute != []:
        # Save current sub-route before return if not empty
        route.append(subRoute)
    
    # Debug Code:
    printRoute(route)
    # End of Debug

    # Code for creating light resource routes within each subroutes served by a heavy
    
    for subroutes in route:
        # Initialize lightSubRoute, heavySubRoute, subRoute
        # Careful: do not change the iterator size. So create heavy subroute and light subroute and update the
        # entire route with it.
        lightSubRoute = []
        heavySubRoute = []
        subRoute = []
        lightVehicleLoad = 0
        lightElapsedTime = 0
        lightTravelRange = 0
        # Assumption: from the second customer in subRoute, group any consecutive
        # customers with total travel range less than 20 (subject to change, simple 
        # implmentation) and within capacity constraint.
        # Time window is not considered at the moment
        lastCustomerID = 0
        for customerID in subroutes:
            # Debug Code:
            print("the current subroute is:")
            print(subroutes)
            print("Last customer ID: " + str(lastCustomerID))
            print("Current customer ID: " + str(customerID))
            # End of Debug
            # Update light vehicle load
            demand = instance['customer_%d' % customerID]['demand']
            updatedLightVehicleLoad = lightVehicleLoad + demand
            # Update light travel range
            travelTime = instance['distance_matrix'][lastCustomerID][customerID]
            updatedLightTravelRange = lightTravelRange + travelTime
            
            # Add skipped customer into the heavySubRoute list
            if heavySubRoute == []:
                heavySubRoute.append(customerID)
                print("Appended the first customer into heavySubRoute:")
                print(heavySubRoute)
        
            # Validate the capacity and travel range constraints
            # TODO maybe constrain the lightSubRoute to be of a length that is more than 2 customers?
            elif (updatedLightVehicleLoad <= lightVehicleCapcity) and (updatedLightTravelRange <= lightVehicleRange):
                # Add to the current lightSubRoute
                lightSubRoute.append(customerID)
                lightVehicleLoad = updatedLightVehicleLoad
                lightTravelRange = updatedLightTravelRange
                print("Appended the current customer into lightSubRoute:")
                print(lightSubRoute)
                
            else:
                # Save the current lightSubRoute
                # i.e. subRoute = [7,8,9,19,21]; lightSubRoute = [8,9]; heavySubRoute = [7], [19,21]
                # subRoute = [[7],[8,9],[19,21]]
                print("Current light load is: %d" % updatedLightVehicleLoad)
                print("Current light range is: %d" % updatedLightTravelRange)

                if lightSubRoute == []:
                    heavySubRoute.append(customerID)
                    print("Appended the current customer into heavySubRoute:")
                    print(heavySubRoute)
                elif lightSubRoute != []:
                    subRoute.append(heavySubRoute)
                    subRoute.append(lightSubRoute)
                    subRoute.append([customerID])
                    print("Appended the light and heavy routes into subRoute")
                    print(subRoute)

                    # Clean both light/heavySubRoutes
                    lightSubRoute = []
                    heavySubRoute = []
                    lightTravelRange = 0
                    lightVehicleLoad = 0

                # Assupmtion: skip over 1 customer if a lightSubRoute was formed
                # so there is a space for the light vehicle to "reunite" with the heavy vehicle. 
            lastCustomerID = customerID

            # Update elapsed time
            # This is slightly different from the heavy vehicle formulation because the light
            # vehicle recombines with the heavy vehicle and not back to depot. Therefore, the
            # return time should be the time from the last customer in the light resource
            # subroute to the customer immediately after in the subroute
            # i.e. [2,3,4,[7,8],10,12], the distance from [8] to [10]
            # Which means this is a potential for inefficiencies because it is not optimized

        # Add the lightSubRoute to the end of the route if not empty, will be treated as heavySubRoute
        if lightSubRoute != [] and heavySubRoute != []:
            if subRoute == []:
                subRoute.append(heavySubRoute)
            else:
                subRoute[-1].extend(heavySubRoute)
            subRoute[-1].extend(lightSubRoute) # extend the last heavySubRoute with the rest of lightSubRoute
            print("Appended the rest of the lightSubRoute as heavySubroute in subRoute")
            print(subRoute)
        # Add the heavySubRoute to the end of route if not empty    
        elif lightSubRoute == [] and heavySubRoute != []:
            subRoute.append(heavySubRoute)
            print("Appended the rest of the heavySubRoute in subRoute")
        else:
            pass
        
        # Add the finalized subRoute into routeWithTwoResources
        routeWithTwoResources.append(subRoute)
        print("routeWithTwoResources looks like:")
        print(routeWithTwoResources)

    return routeWithTwoResources


def printRoute(route, merge=False, twoResources=False):
    routeStr = '0'
    subRouteCount = 0
    for subRoute in route:
        subRouteCount += 1
        subSubRouteCount = 0
        subRouteStr = '0'
        heavyRouteStr = '0'
        lightRouteStr = ''
        if twoResources:
            for subSubRoute in subRoute:
                subSubRouteCount += 1
                for customerID in subSubRoute:
                    # A lightSubRoute
                    if subSubRouteCount % 3 == 2:
                        lightRouteStr = lightRouteStr + ' - ' + str(customerID)
                        subRouteStr = subRouteStr + ' - ' + str(customerID)
                        routeStr = routeStr + ' - ' + str(customerID)
                    # A heavySubRoute
                    elif subSubRouteCount % 3 == 1 or subSubRouteCount % 3 == 0:
                        heavyRouteStr = heavyRouteStr + ' - ' + str(customerID)
                        subRouteStr = subRouteStr + ' - ' + str(customerID)
                        routeStr = routeStr + ' - ' + str(customerID)
                # Replace the lightSubRoute as a 'L' in heavySubRoute
                if subSubRouteCount % 3 == 2:
                    heavyRouteStr = heavyRouteStr + ' - L'
                # Replace the heavySubRoute as a 'H' in heavySubRoute
                elif subSubRouteCount % 3 == 1 or subSubRouteCount % 3 == 0:
                    lightRouteStr = lightRouteStr + ' - H'
                
            heavyRouteStr = heavyRouteStr + ' - 0'
            subRouteStr = subRouteStr + ' - 0'

            if not merge:
                print '  Vehicle %d\'s route: %s ' % (subRouteCount, subRouteStr)
                print '  Vehicle %d\'s heavy resource route %s ' % (subRouteCount, heavyRouteStr)
                print '  Vehicle %d\'s light resource route %s ' % (subRouteCount, lightRouteStr)
                                

        else:
            for customerID in subRoute:
                subRouteStr = subRouteStr + ' - ' + str(customerID)
                routeStr = routeStr + ' - ' + str(customerID)
            subRouteStr = subRouteStr + ' - 0'
            if not merge:
                print '  Vehicle %d\'s route: %s' % (subRouteCount, subRouteStr)
                routeStr = routeStr + ' - 0'
        if merge:
            print routeStr

    return

def evalVRPTW(individual, instance, unitCost=1.0, initCost=0, waitCost=0, delayCost=0,
                                    lightUnitCost=1.0, lightInitCost=0, lightWaitCost=0, lightDelayCost=0):
    route = ind2route(individual, instance)
    totalCost = 0
    totalCostTwoResource = 0
    for subRoute in route:
        subRouteTimeCost = 0
        subRouteDistance = 0

        elapsedTime = 0
        lastCustomerID = 0

        subSubRouteCount = 0
        lightSubRouteDistance = 0
        heavySubRouteDistance = 0
        lightElapsedTime = 0
        heavyElapsedTime = 0
        for subSubRoute in subRoute:
            subSubRouteCount += 1
            lightSubRouteTimeCost = 0
            heavySubRouteTimeCost = 0

            # Set binary variable isLightSubRoute to true if subSubRoute is served by light resource
            if subSubRouteCount % 3 == 2: 
                isLightSubRoute = True
            else:
                isLightSubRoute = False
            isHeavySubRoute = not isLightSubRoute

            for customerID in subSubRoute:
                # Calculate section distance
                distance = instance['distance_matrix'][lastCustomerID][customerID]
                # Update sub-route distance
                subRouteDistance = subRouteDistance + distance
                # Update heavy/light-SubRoute distance
                lightSubRouteDistance = lightSubRouteDistance + (distance * isLightSubRoute)
                heavySubRouteDistance = heavySubRouteDistance + (distance * isHeavySubRoute)
                # Calculate time cost
                arrivalTime = elapsedTime + distance
                timeCost = waitCost * max(instance['customer_%d' % customerID]['ready_time'] - arrivalTime, 0) + delayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)
                # Calculate light-SubRoute specific time cost
                lightTimeCost = (lightWaitCost * max(instance['customer_%d' % customerID]['ready_time'] - arrivalTime, 0) + lightDelayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)) * isLightSubRoute
                # Update sub-route time cost
                subRouteTimeCost = subRouteTimeCost + timeCost
                # Udpate heavy/light-SubRoute time cost
                lightSubRouteTimeCost = lightSubRouteTimeCost + lightTimeCost
                heavySubRouteTimeCost = heavySubRouteTimeCost + timeCost * isHeavySubRoute
                # Update elapsed time
                elapsedTime = arrivalTime + instance['customer_%d' % customerID]['service_time']
                # Update last customer ID
                lastCustomerID = customerID

        # Calculate transport cost
        subRouteDistance = subRouteDistance + instance['distance_matrix'][lastCustomerID][0]
        subRouteTranCost = initCost + unitCost * subRouteDistance
        # Calculate heavy/light transport cost
        lightSubRouteTransCost = lightInitCost + lightUnitCost * lightSubRouteDistance
        heavySubRouteDistance = heavySubRouteDistance + instance['distance_matrix'][lastCustomerID][0]
        heavySubRouteTransCost = initCost + unitCost * heavySubRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTimeCost + subRouteTranCost
        # Obtain heavy/light subRoute cost
        lightSubRouteCost = lightSubRouteTimeCost + lightSubRouteTransCost
        heavySubRouteCost = heavySubRouteTimeCost + heavySubRouteTransCost
        # Update total cost
        totalCost = totalCost + subRouteCost
        # Update total cost with 2 resources
        totalCostTwoResource = totalCostTwoResource + lightSubRouteCost + heavySubRouteCost
        # Debug
        print ("The total cost is: %d" % totalCost)
        print ("The total cost with 2 resources is: %d, with light costing: %d, and heavy costing: %d" % (totalCostTwoResource, lightSubRouteCost, heavySubRouteCost))
        # End of Debug
    fitness = 1.0 / totalCostTwoResource
    return fitness,


def cxPartialyMatched(ind1, ind2):
    size = min(len(ind1), len(ind2))
    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
    temp1 = ind1[cxpoint1:cxpoint2+1] + ind2
    temp2 = ind1[cxpoint1:cxpoint2+1] + ind1
    ind1 = []
    for x in temp1:
        if x not in ind1:
            ind1.append(x)
    ind2 = []
    for x in temp2:
        if x not in ind2:
            ind2.append(x)
    return ind1, ind2


def mutInverseIndexes(individual):
    start, stop = sorted(random.sample(range(len(individual)), 2))
    individual = individual[:start] + individual[stop:start-1:-1] + individual[stop+1:]
    return individual,


def gaVRPTW(instName, unitCost, initCost, waitCost, delayCost, indSize, popSize, cxPb, mutPb, NGen, exportCSV=False, customizeData=False):
    if customizeData:
        jsonDataDir = os.path.join(BASE_DIR,'data', 'json_customize')
    else:
        jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
    jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
    with open(jsonFile) as f:
        instance = load(f)
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    # Attribute generator
    toolbox.register('indexes', random.sample, range(1, indSize + 1), indSize)
    # Structure initializers
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indexes)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    # Operator registering
    toolbox.register('evaluate', evalVRPTW, instance=instance, unitCost=unitCost, initCost=initCost, waitCost=waitCost, delayCost=delayCost)
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', cxPartialyMatched)
    toolbox.register('mutate', mutInverseIndexes)
    pop = toolbox.population(n=popSize)
    # Results holders for exporting results to CSV file
    csvData = []
    print 'Start of evolution'
    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    print '  Evaluated %d individuals' % len(pop)
    # Begin the evolution
    for g in range(NGen):
        print '-- Generation %d --' % g
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxPb:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        for mutant in offspring:
            if random.random() < mutPb:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness
        invalidInd = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
        print '  Evaluated %d individuals' % len(invalidInd)
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5
        print '  Min %s' % min(fits)
        print '  Max %s' % max(fits)
        print '  Avg %s' % mean
        print '  Std %s' % std
        # Write data to holders for exporting results to CSV file
        if exportCSV:
            csvRow = {
                'generation': g,
                'evaluated_individuals': len(invalidInd),
                'min_fitness': min(fits),
                'max_fitness': max(fits),
                'avg_fitness': mean,
                'std_fitness': std,
            }
            csvData.append(csvRow)
    print '-- End of (successful) evolution --'
    bestInd = tools.selBest(pop, 1)[0]
    print 'Best individual: %s' % bestInd
    print 'Fitness: %s' % bestInd.fitness.values[0]
    printRoute(ind2route(bestInd, instance))
    print 'Total cost: %s' % (1 / bestInd.fitness.values[0])
    if exportCSV:
        csvFilename = '%s_uC%s_iC%s_wC%s_dC%s_iS%s_pS%s_cP%s_mP%s_nG%s.csv' % (instName, unitCost, initCost, waitCost, delayCost, indSize, popSize, cxPb, mutPb, NGen)
        csvPathname = os.path.join(BASE_DIR, 'results', csvFilename)
        print 'Write to file: %s' % csvPathname
        makeDirsForFile(pathname=csvPathname)
        if not exist(pathname=csvPathname, overwrite=True):
            with open(csvPathname, 'w') as f:
                fieldnames = ['generation', 'evaluated_individuals', 'min_fitness', 'max_fitness', 'avg_fitness', 'std_fitness']
                writer = DictWriter(f, fieldnames=fieldnames, dialect='excel')
                writer.writeheader()
                for csvRow in csvData:
                    writer.writerow(csvRow)